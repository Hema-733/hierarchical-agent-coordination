"""
services/workflow_service.py — Manages workflow creation, status tracking, and pause/resume.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from app.models.workflow import WorkflowStatus, WorkflowType, WorkflowResponse
from app.models.task import TaskResponse, TaskStatus
from app.db.repositories import workflow_repo, task_repo
from app.services import task_service
from app.services.event_broker import event_broker


def generate_workflow_id() -> str:
    """Generates a unique Workflow ID."""
    return f"WF-{uuid.uuid4().hex[:6].upper()}"


async def create_onboarding_workflow(employee_id: str) -> WorkflowResponse:
    """
    Creates a new onboarding workflow and initializes the required tasks.
    """
    workflow_id = generate_workflow_id()
    doc = {
        "workflow_id": workflow_id,
        "employee_id": employee_id,
        "workflow_type": WorkflowType.EMPLOYEE_ONBOARDING.value,
        "overall_status": WorkflowStatus.PENDING.value,
        "metadata": {}
    }

    saved_wf = await workflow_repo.create_workflow(doc)
    tasks = await task_service.initialize_onboarding_tasks(workflow_id)

    return WorkflowResponse(**saved_wf, tasks=tasks)


async def get_workflow_details(workflow_id: str, include_tasks: bool = True) -> WorkflowResponse:
    """Retrieves full workflow details including associated tasks and employee info."""
    wf = await workflow_repo.get_workflow_by_id(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found."
        )

    tasks: Optional[List[TaskResponse]] = None
    if include_tasks:
        task_list = await task_repo.get_tasks_by_workflow(workflow_id)
        tasks = [TaskResponse(**t) for t in task_list]

    from app.db.repositories import employee_repo
    employee = None
    if wf.get("employee_id"):
        employee = await employee_repo.get_employee_by_id(wf["employee_id"])

    return WorkflowResponse(**wf, tasks=tasks, employee=employee)


async def list_workflows(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None
) -> List[WorkflowResponse]:
    """Lists workflows with optional status filtering and enriched candidate data for the queue."""
    from app.db.repositories import employee_repo
    wf_list = await workflow_repo.list_workflows(skip=skip, limit=limit, status=status_filter)
    results = []
    for wf in wf_list:
        emp_id = wf.get("employee_id")
        emp = None
        if emp_id:
            emp = await employee_repo.get_employee_by_id(emp_id)
        task_list = await task_repo.get_tasks_by_workflow(wf["workflow_id"])
        tasks = [TaskResponse(**t) for t in task_list]
        results.append(WorkflowResponse(**wf, tasks=tasks, employee=emp))
    return results


async def pause_workflow(workflow_id: str, reason: Optional[str] = None) -> WorkflowResponse:
    """
    Pauses a RUNNING or PENDING workflow.

    Records paused_at timestamp and reason in the document.
    The Supervisor loop will detect the PAUSED flag at its next checkpoint
    and stop execution cleanly without losing task state.
    """
    wf = await workflow_repo.get_workflow_by_id(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found."
        )

    allowed_to_pause = {
        WorkflowStatus.RUNNING.value,
        WorkflowStatus.PENDING.value,
        WorkflowStatus.ACTION_REQUIRED.value
    }
    if wf["overall_status"] not in allowed_to_pause:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Only RUNNING, PENDING, or ACTION_REQUIRED workflows can be paused. "
                f"Current status: {wf['overall_status']}."
            )
        )

    pause_reason = reason or "Paused by administrator."
    now = datetime.utcnow()

    collection = workflow_repo._get_collection()
    updated = await collection.find_one_and_update(
        {"workflow_id": workflow_id},
        {
            "$set": {
                "overall_status": WorkflowStatus.PAUSED.value,
                "paused_at": now,
                "paused_reason": pause_reason,
                "updated_at": now
            }
        },
        projection={"_id": 0},
        return_document=True
    )

    task_list = await task_repo.get_tasks_by_workflow(workflow_id)
    print(f"[WorkflowService] Workflow '{workflow_id}' PAUSED. Reason: {pause_reason}")
    event_broker.publish(
        workflow_id=workflow_id,
        event_type="WORKFLOW_PAUSED",
        message=f"Workflow paused. Reason: {pause_reason}",
        status="PAUSED",
        data={"paused_reason": pause_reason},
    )
    return WorkflowResponse(**updated, tasks=[TaskResponse(**t) for t in task_list])


async def resume_workflow(workflow_id: str) -> WorkflowResponse:
    """
    Resumes a PAUSED or ACTION_REQUIRED workflow back to RUNNING.

    Records resumed_at timestamp and clears the pause reason.
    The Supervisor is then re-invoked externally (from the API layer)
    to pick up remaining READY/PENDING tasks.
    """
    wf = await workflow_repo.get_workflow_by_id(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found."
        )

    allowed_to_resume = {
        WorkflowStatus.PAUSED.value,
        WorkflowStatus.ACTION_REQUIRED.value
    }
    if wf["overall_status"] not in allowed_to_resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Only PAUSED or ACTION_REQUIRED workflows can be resumed. "
                f"Current status is {wf['overall_status']}."
            )
        )

    now = datetime.utcnow()
    collection = workflow_repo._get_collection()
    updated = await collection.find_one_and_update(
        {"workflow_id": workflow_id},
        {
            "$set": {
                "overall_status": WorkflowStatus.RUNNING.value,
                "resumed_at": now,
                "paused_reason": None,
                "updated_at": now
            }
        },
        projection={"_id": 0},
        return_document=True
    )

    task_list = await task_repo.get_tasks_by_workflow(workflow_id)
    # Unblock any tasks that were PAUSED waiting for human document verification
    for t in task_list:
        if t.get("status") == TaskStatus.PAUSED.value:
            await task_repo.update_task_status(
                task_id=t["task_id"],
                status=TaskStatus.READY.value,
                error_message=None
            )
            await task_repo._get_collection().update_one(
                {"task_id": t["task_id"]},
                {"$set": {"retry_count": 0}}
            )
            t["status"] = TaskStatus.READY.value
            t["retry_count"] = 0
            t["error_message"] = None

    print(f"[WorkflowService] Workflow '{workflow_id}' RESUMED at {now.isoformat()}")
    event_broker.publish(
        workflow_id=workflow_id,
        event_type="WORKFLOW_RESUMED",
        message="Workflow resumed by operator. Continuing multi-agent coordination.",
        status="RUNNING",
    )
    return WorkflowResponse(**updated, tasks=[TaskResponse(**t) for t in task_list])
