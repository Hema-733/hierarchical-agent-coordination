"""
services/summary_service.py — Workflow Status Summary.

Computes a rich summary report for a workflow:
  - Overall progress percentage
  - Per-status task counts
  - Per-agent contribution breakdown
  - Timeline of task execution with durations
  - Failure diagnostics
  - Estimated completion metadata
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.db.repositories import workflow_repo, task_repo, employee_repo


def _parse_dt(value) -> Optional[datetime]:
    """Safely parse a datetime value (str or datetime) to a timezone-aware datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None
    return None


def _duration_seconds(start, end) -> Optional[float]:
    """Returns elapsed seconds between two datetime values."""
    s = _parse_dt(start)
    e = _parse_dt(end)
    if s and e:
        return round((e - s).total_seconds(), 2)
    return None


async def get_workflow_summary(workflow_id: str) -> Dict[str, Any]:
    """
    Generates a comprehensive status summary for a given workflow.

    Returns:
        {
            workflow_id, employee, overall_status, progress_pct,
            task_counts, agent_contributions, timeline, failures,
            timing, generated_at
        }
    """
    # ── Fetch core data ──────────────────────────────────────────
    wf = await workflow_repo.get_workflow_by_id(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found."
        )

    tasks: List[Dict[str, Any]] = await task_repo.get_tasks_by_workflow(workflow_id)
    employee = await employee_repo.get_employee_by_id(wf.get("employee_id", "")) or {}

    total = len(tasks)

    # ── Task counts by status ────────────────────────────────────
    counts: Dict[str, int] = {
        "PENDING": 0, "READY": 0, "RUNNING": 0,
        "COMPLETED": 0, "FAILED": 0
    }
    for t in tasks:
        s = t.get("status", "PENDING")
        counts[s] = counts.get(s, 0) + 1

    completed_count = counts["COMPLETED"]
    progress_pct = round((completed_count / total) * 100, 1) if total > 0 else 0.0

    # ── Timeline: one entry per task ────────────────────────────
    timeline: List[Dict[str, Any]] = []
    for t in tasks:
        started_at = _parse_dt(t.get("started_at"))
        completed_at = _parse_dt(t.get("completed_at"))
        duration = _duration_seconds(started_at, completed_at)

        entry: Dict[str, Any] = {
            "task_id": t.get("task_id"),
            "task_name": t.get("task_name"),
            "agent": t.get("agent"),
            "status": t.get("status"),
            "retry_count": t.get("retry_count", 0),
            "max_retries": t.get("max_retries", 3),
            "started_at": started_at.isoformat() if started_at else None,
            "completed_at": completed_at.isoformat() if completed_at else None,
            "duration_seconds": duration,
        }
        timeline.append(entry)

    # ── Agent contributions ──────────────────────────────────────
    agent_contrib: Dict[str, Dict[str, Any]] = {}
    for t in tasks:
        agent_name = t.get("agent", "Unknown")
        if agent_name not in agent_contrib:
            agent_contrib[agent_name] = {
                "tasks_assigned": 0,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "total_retries": 0,
                "total_duration_seconds": 0.0
            }
        agent_contrib[agent_name]["tasks_assigned"] += 1
        if t.get("status") == "COMPLETED":
            agent_contrib[agent_name]["tasks_completed"] += 1
        elif t.get("status") == "FAILED":
            agent_contrib[agent_name]["tasks_failed"] += 1
        agent_contrib[agent_name]["total_retries"] += t.get("retry_count", 0)
        d = _duration_seconds(t.get("started_at"), t.get("completed_at"))
        if d:
            agent_contrib[agent_name]["total_duration_seconds"] += round(d, 2)

    # ── Failure diagnostics ──────────────────────────────────────
    failures: List[Dict[str, Any]] = []
    for t in tasks:
        if t.get("status") == "FAILED":
            failures.append({
                "task_id": t.get("task_id"),
                "task_name": t.get("task_name"),
                "agent": t.get("agent"),
                "error_message": t.get("error_message"),
                "retry_count": t.get("retry_count", 0),
                "max_retries": t.get("max_retries", 3),
                "retries_exhausted": t.get("retry_count", 0) >= t.get("max_retries", 3)
            })

    # ── Overall timing ───────────────────────────────────────────
    wf_created = _parse_dt(wf.get("created_at"))
    wf_updated = _parse_dt(wf.get("updated_at"))
    total_elapsed = _duration_seconds(wf_created, wf_updated)

    timing: Dict[str, Any] = {
        "workflow_created_at": wf_created.isoformat() if wf_created else None,
        "workflow_updated_at": wf_updated.isoformat() if wf_updated else None,
        "total_elapsed_seconds": total_elapsed,
        "paused_at": wf.get("paused_at").isoformat() if _parse_dt(wf.get("paused_at")) else None,
        "paused_reason": wf.get("paused_reason"),
        "resumed_at": wf.get("resumed_at").isoformat() if _parse_dt(wf.get("resumed_at")) else None,
    }

    return {
        "workflow_id": workflow_id,
        "workflow_type": wf.get("workflow_type"),
        "overall_status": wf.get("overall_status"),
        "employee": {
            "employee_id": employee.get("employee_id"),
            "employee_name": employee.get("employee_name"),
            "department": employee.get("department"),
            "designation": employee.get("designation"),
        },
        "progress": {
            "total_tasks": total,
            "completed": completed_count,
            "progress_pct": progress_pct,
            "task_counts": counts,
        },
        "agent_contributions": agent_contrib,
        "timeline": timeline,
        "failures": failures,
        "timing": timing,
        "generated_at": datetime.utcnow().isoformat()
    }
