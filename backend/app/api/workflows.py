"""
api/workflows.py — API Router for Workflow Management.

Provides endpoints for:
- Querying workflow status and task progress
- Listing workflows (with status filter)
- Executing/Triggering the Supervisor orchestration loop
- Pausing a RUNNING workflow
- Resuming a PAUSED workflow
- Real-time SSE event streaming for a workflow
"""

import asyncio
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Body, Query, HTTPException, Request, status
from sse_starlette.sse import EventSourceResponse
from app.models.workflow import WorkflowResponse, WorkflowStatus
from app.services import workflow_service, summary_service, gemini_service
from app.agents.supervisor_agent import supervisor_agent
from app.services.event_broker import event_broker

router = APIRouter()


@router.get(
    "/",
    response_model=List[WorkflowResponse],
    summary="List all workflows",
    description="Returns workflows with optional filtering by status (PENDING, RUNNING, PAUSED, COMPLETED, FAILED)."
)
async def list_workflows(
    status: Optional[WorkflowStatus] = Query(None, description="Filter workflows by overall status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return")
):
    """Lists all workflows in the system."""
    status_str = status.value if status else None
    return await workflow_service.list_workflows(skip=skip, limit=limit, status_filter=status_str)


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get workflow details and task progress"
)
async def get_workflow(workflow_id: str):
    """Retrieves full workflow details and all associated tasks."""
    return await workflow_service.get_workflow_details(workflow_id=workflow_id, include_tasks=True)


@router.post(
    "/{workflow_id}/execute",
    summary="Trigger Supervisor execution loop for a workflow",
    description="Invokes the Supervisor Agent to evaluate ready tasks, delegate execution to specialized agents, and advance the workflow."
)
async def execute_workflow(workflow_id: str) -> Dict[str, Any]:
    """Triggers the Supervisor Agent to orchestrate and execute tasks."""
    try:
        result = await supervisor_agent.run_workflow(workflow_id)
        wf_details = await workflow_service.get_workflow_details(workflow_id)
        return {
            "execution_summary": result,
            "workflow": wf_details
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{workflow_id}/pause",
    response_model=WorkflowResponse,
    summary="Pause a running workflow",
    description="Pauses a RUNNING or PENDING workflow. The Supervisor will stop at its next checkpoint. Pass an optional reason in the request body."
)
async def pause_workflow(
    workflow_id: str,
    reason: Optional[str] = Body(default=None, embed=True, description="Human-readable reason for pausing")
):
    """
    Pauses a workflow. The Supervisor loop will detect the PAUSED status
    at its next iteration checkpoint and stop cleanly.
    """
    return await workflow_service.pause_workflow(workflow_id=workflow_id, reason=reason)


@router.post(
    "/{workflow_id}/resume",
    response_model=WorkflowResponse,
    summary="Resume a paused workflow",
    description="Resumes a PAUSED workflow back to RUNNING and re-triggers the Supervisor to continue from where it stopped."
)
async def resume_workflow(workflow_id: str):
    """Resumes a workflow from PAUSED state and re-triggers the Supervisor."""
    # Transition the workflow state first
    wf = await workflow_service.resume_workflow(workflow_id)
    # Re-invoke Supervisor to pick up remaining ready tasks
    await supervisor_agent.run_workflow(workflow_id)
    return await workflow_service.get_workflow_details(workflow_id)


@router.get(
    "/{workflow_id}/summary",
    summary="Get a rich workflow status summary",
    description=(
        "Returns a comprehensive summary: overall progress %, task counts by status, "
        "per-agent contribution breakdown, execution timeline with durations, "
        "failure diagnostics, and timing metadata."
    )
)
async def get_workflow_summary(workflow_id: str) -> Dict[str, Any]:
    """
    Aggregates and returns a full status report for the given workflow.
    Useful for dashboards, reporting, and debugging orchestration issues.
    """
    return await summary_service.get_workflow_summary(workflow_id)


@router.get(
    "/{workflow_id}/ai-summary",
    summary="Generate an AI narrative for workflow status",
    description=(
        "Uses Gemini to produce a natural-language onboarding status update that "
        "an HR manager could share with their team. Degrades gracefully to a "
        "deterministic fallback if the API key is not configured."
    )
)
async def get_ai_workflow_summary(workflow_id: str) -> Dict[str, Any]:
    """
    Fetches the structured workflow summary, then passes it to Gemini
    to generate a professional onboarding status narrative.
    """
    wf_summary = await summary_service.get_workflow_summary(workflow_id)
    ai_result = await gemini_service.generate_onboarding_summary(wf_summary)
    return {
        **ai_result,
        "workflow_id": workflow_id,
        "overall_status": wf_summary["overall_status"],
        "progress_pct": wf_summary["progress"]["progress_pct"],
        "employee": wf_summary["employee"]
    }


@router.get(
    "/{workflow_id}/stream",
    summary="Stream real-time workflow events via Server-Sent Events",
    description=(
        "Opens a persistent SSE connection for the given workflow. "
        "Replays recent buffered events first (so late-joiners are not blind), "
        "then streams all future events in real time until the workflow completes "
        "or the client disconnects."
    ),
)
async def stream_workflow_events(workflow_id: str, request: Request):
    """
    SSE endpoint — one connection per client per workflow.
    Event schema (JSON-encoded in the 'data' field):
      {
        "id": "evt_<workflow_id>_<ts>_<seq>",
        "workflow_id": "<id>",
        "timestamp": "<ISO8601>",
        "type": "WORKFLOW_STARTED | ROUND_STARTED | TASK_READY | AGENT_TASK_STARTED |
                  AGENT_TASK_COMPLETED | TASK_FAILED | TASK_RETRYING |
                  WORKFLOW_COMPLETED | WORKFLOW_PAUSED | WORKFLOW_RESUMED",
        "agent": "<agent name>",
        "task_id": "<id or null>",
        "task_name": "<name or null>",
        "status": "<status string>",
        "round": <int or null>,
        "message": "<human-readable description>",
        "data": {}
      }
    """
    # Verify the workflow exists before opening a connection
    wf = await workflow_service.get_workflow_details(workflow_id, include_tasks=False)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")

    async def event_generator():
        queue, history = event_broker.subscribe(workflow_id)
        try:
            # ── Replay buffered history so late-joining clients see past events ──
            for past_event in history:
                if await request.is_disconnected():
                    return
                yield {
                    "event": past_event["type"],
                    "id": past_event["id"],
                    "data": json.dumps(past_event),
                }

            # ── Stream live events ──
            while True:
                if await request.is_disconnected():
                    return
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25.0)
                    yield {
                        "event": event["type"],
                        "id": event["id"],
                        "data": json.dumps(event),
                    }
                    # Stop streaming once the workflow reaches a terminal state
                    if event["type"] in ("WORKFLOW_COMPLETED", "TASK_FAILED") and event.get("status") in ("COMPLETED", "FAILED"):
                        return
                except asyncio.TimeoutError:
                    # Send a keep-alive comment to prevent proxy timeouts
                    yield {"event": "ping", "data": json.dumps({"type": "ping"})}
        finally:
            event_broker.unsubscribe(workflow_id, queue)

    return EventSourceResponse(event_generator())
