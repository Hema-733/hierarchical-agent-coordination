"""
services/gemini_service.py — Gemini LLM Integration (google-genai SDK).

Powers two AI capabilities:
  1. generate_onboarding_summary()  — Natural-language narrative of a completed workflow
  2. explain_task_failure()          — Plain-English explanation of a failed task + fix guidance

Both functions degrade gracefully: if the API key is missing or the call fails,
they return deterministic fallback text instead of raising exceptions.
"""

import json
from typing import Dict, Any, Optional
from app.config import settings

# ── Lazy initialisation ──────────────────────────────────────────────────────
# We import at function call time so the server still starts without a key.

def _get_client():
    """Returns an initialised google-genai Client, or None if key is absent."""
    try:
        from google import genai  # type: ignore
        api_key = settings.GEMINI_API_KEY.strip()
        if not api_key or api_key == "your_gemini_api_key_here":
            return None
        return genai.Client(api_key=api_key)
    except Exception:
        return None


MODEL = "gemini-2.0-flash"


# ── Prompt builders ──────────────────────────────────────────────────────────

def _build_onboarding_summary_prompt(summary: Dict[str, Any]) -> str:
    emp = summary.get("employee", {})
    prog = summary.get("progress", {})
    timing = summary.get("timing", {})
    failures = summary.get("failures", [])
    timeline = summary.get("timeline", [])

    task_lines = "\n".join(
        f"  - {t['task_name']} ({t['agent']}): {t['status']}"
        + (f", retries={t['retry_count']}" if t.get("retry_count", 0) > 0 else "")
        for t in timeline
    )

    failure_lines = ""
    if failures:
        failure_lines = "\nFailed tasks:\n" + "\n".join(
            f"  - {f['task_name']}: {f['error_message']} (retries exhausted: {f['retries_exhausted']})"
            for f in failures
        )

    return f"""You are an AI assistant for an enterprise HR system.

An employee onboarding workflow has just completed. Write a concise, professional 
onboarding status update (2-4 sentences) that an HR manager could send to their team.
Focus on what was accomplished, highlight any issues, and keep the tone warm but factual.
Do NOT use bullet points. Write in plain prose.

ONBOARDING DETAILS:
Employee: {emp.get('employee_name')} 
Department: {emp.get('department')} 
Designation: {emp.get('designation')}
Overall Status: {summary.get('overall_status')}
Progress: {prog.get('progress_pct')}% ({prog.get('completed')}/{prog.get('total_tasks')} tasks completed)
Total Time: {timing.get('total_elapsed_seconds')}s

Tasks executed:
{task_lines}
{failure_lines}

Write the status update now:"""


def _build_failure_explanation_prompt(task: Dict[str, Any], employee: Dict[str, Any]) -> str:
    return f"""You are an AI assistant for an enterprise HR system.

A task in an employee onboarding workflow has failed. Explain the failure clearly 
in 2-3 sentences: what went wrong, why it matters, and what the HR administrator 
needs to do to fix it. Be specific and actionable. Do NOT use bullet points.

FAILED TASK DETAILS:
Task Name: {task.get('task_name')}
Assigned Agent: {task.get('agent')}
Error Message: {task.get('error_message')}
Retry Count: {task.get('retry_count')} / {task.get('max_retries')} (retries exhausted: {task.get('retry_count', 0) >= task.get('max_retries', 3)})

EMPLOYEE CONTEXT:
Name: {employee.get('employee_name')}
Department: {employee.get('department')}
Designation: {employee.get('designation')}

Write the failure explanation now:"""


# ── Public API ───────────────────────────────────────────────────────────────

async def generate_onboarding_summary(workflow_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls Gemini to generate a natural-language onboarding status update.

    Returns:
        {
            "ai_summary": str,        # Gemini-generated or fallback text
            "ai_available": bool,     # Whether Gemini was actually called
            "model": str              # Model used
        }
    """
    client = _get_client()

    if not client:
        # Deterministic fallback
        emp = workflow_summary.get("employee", {})
        prog = workflow_summary.get("progress", {})
        status = workflow_summary.get("overall_status", "UNKNOWN")
        fallback = (
            f"Onboarding workflow for {emp.get('employee_name', 'the employee')} "
            f"({emp.get('department')}) has reached status: {status}. "
            f"{prog.get('completed', 0)} of {prog.get('total_tasks', 0)} tasks completed "
            f"({prog.get('progress_pct', 0)}%). "
            f"Please review the workflow details for full task-level information."
        )
        return {"ai_summary": fallback, "ai_available": False, "model": "fallback"}

    try:
        prompt = _build_onboarding_summary_prompt(workflow_summary)
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return {
            "ai_summary": response.text.strip(),
            "ai_available": True,
            "model": MODEL
        }
    except Exception as exc:
        return {
            "ai_summary": f"AI summary unavailable ({str(exc)[:80]}). Please review workflow details directly.",
            "ai_available": False,
            "model": "fallback"
        }


async def explain_task_failure(
    task: Dict[str, Any],
    employee: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calls Gemini to explain a failed task in plain English with fix guidance.

    Returns:
        {
            "explanation": str,       # Gemini-generated or fallback explanation
            "ai_available": bool,
            "model": str
        }
    """
    client = _get_client()

    if not client:
        error_msg = task.get("error_message", "Unknown error")
        fallback = (
            f"The '{task.get('task_name')}' task failed with the following error: "
            f"{error_msg}. "
            f"Please review the error details above and take corrective action "
            f"before retrying the workflow."
        )
        return {"explanation": fallback, "ai_available": False, "model": "fallback"}

    try:
        prompt = _build_failure_explanation_prompt(task, employee)
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return {
            "explanation": response.text.strip(),
            "ai_available": True,
            "model": MODEL
        }
    except Exception as exc:
        return {
            "explanation": f"AI explanation unavailable ({str(exc)[:80]}). Error: {task.get('error_message')}",
            "ai_available": False,
            "model": "fallback"
        }
