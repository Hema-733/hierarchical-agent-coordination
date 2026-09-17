"""
services/task_service.py — Manages task lifecycle, status transitions, and dependency graphs.
"""

import uuid
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from app.models.task import TaskStatus, TaskResponse
from app.db.repositories import task_repo


def generate_task_id() -> str:
    """Generates a human-friendly unique task ID."""
    return f"TSK-{uuid.uuid4().hex[:6].upper()}"


# Standard Onboarding Workflow Task Templates with defined dependencies
ONBOARDING_TASK_TEMPLATES = [
    {
        "task_name": "HR Verification",
        "agent": "HR Agent",
        "dependencies": [],  # Root task, immediately READY
        "initial_status": TaskStatus.READY
    },
    {
        "task_name": "Document Verification",
        "agent": "HR Agent",
        "dependencies": ["HR Verification"],
        "initial_status": TaskStatus.PENDING
    },
    {
        "task_name": "IT Account Setup",
        "agent": "IT Agent",
        "dependencies": ["Document Verification"],
        "initial_status": TaskStatus.PENDING
    },
    {
        "task_name": "Payroll Setup",
        "agent": "Finance Agent",
        "dependencies": ["Document Verification"],
        "initial_status": TaskStatus.PENDING
    },
    {
        "task_name": "Resource Allocation",
        "agent": "Resource / Admin Agent",
        "dependencies": ["Document Verification"],
        "initial_status": TaskStatus.PENDING
    },
    {
        "task_name": "Final Confirmation",
        "agent": "Supervisor Agent",
        "dependencies": ["IT Account Setup", "Payroll Setup", "Resource Allocation"],
        "initial_status": TaskStatus.PENDING
    }
]


async def initialize_onboarding_tasks(workflow_id: str) -> List[TaskResponse]:
    """
    Instantiates the 6 standard onboarding tasks for a newly created workflow.
    """
    task_docs = []
    for template in ONBOARDING_TASK_TEMPLATES:
        task_docs.append({
            "task_id": generate_task_id(),
            "workflow_id": workflow_id,
            "task_name": template["task_name"],
            "agent": template["agent"],
            "status": template["initial_status"].value,
            "dependencies": template["dependencies"],
            "result": None,
            "error_message": None,
            "retry_count": 0,
            "max_retries": 3,
            "started_at": None,
            "completed_at": None
        })

    created_tasks = await task_repo.create_tasks_batch(task_docs)
    return [TaskResponse(**t) for t in created_tasks]


async def get_workflow_tasks(workflow_id: str) -> List[TaskResponse]:
    """Retrieves all tasks for a workflow."""
    tasks = await task_repo.get_tasks_by_workflow(workflow_id)
    return [TaskResponse(**t) for t in tasks]


async def retry_task(task_id: str) -> TaskResponse:
    """
    Retries a failed task if allowed.
    """
    task = await task_repo.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found."
        )

    if task["status"] != TaskStatus.FAILED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only FAILED tasks can be retried. Current status is {task['status']}."
        )

    if task["retry_count"] >= task.get("max_retries", 3):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task '{task_id}' has exceeded maximum allowed retries ({task.get('max_retries', 3)})."
        )

    updated = await task_repo.increment_task_retry(task_id)
    return TaskResponse(**updated)
