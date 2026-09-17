"""
api/tasks.py — API Router for Task Management.

Provides endpoints for:
- Querying tasks belonging to a workflow
- Inspecting task details and execution logs
- Retrying failed tasks
"""

from typing import List
from fastapi import APIRouter, HTTPException, status
from app.models.task import TaskResponse
from app.services import task_service
from app.db.repositories import task_repo

router = APIRouter()


@router.get(
    "/workflow/{workflow_id}",
    response_model=List[TaskResponse],
    summary="Get all tasks for a workflow"
)
async def get_tasks_for_workflow(workflow_id: str):
    """Retrieves all tasks associated with a workflow."""
    return await task_service.get_workflow_tasks(workflow_id)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task details by task ID"
)
async def get_task(task_id: str):
    """Retrieves execution details and result of a specific task."""
    task = await task_repo.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found."
        )
    return TaskResponse(**task)


@router.post(
    "/{task_id}/retry",
    response_model=TaskResponse,
    summary="Retry a failed task"
)
async def retry_failed_task(task_id: str):
    """
    Retries execution of a FAILED task, setting its status back to READY
    and incrementing the retry counter.
    """
    return await task_service.retry_task(task_id)
