"""
models/task.py — Pydantic models for Workflow Tasks.

Defines schemas and statuses for individual tasks delegated by the Supervisor.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    PAUSED = "PAUSED"


class TaskBase(BaseModel):
    task_name: str = Field(..., description="Name of the task, e.g. 'HR Verification'")
    agent: str = Field(..., description="Assigned agent, e.g. 'HR Agent'")
    dependencies: List[str] = Field(default_factory=list, description="List of prerequisite task names or IDs")


class TaskCreate(TaskBase):
    workflow_id: str = Field(..., description="Associated workflow identifier")
    status: TaskStatus = Field(default=TaskStatus.PENDING)


class TaskInDB(TaskBase):
    task_id: str = Field(..., description="Unique generated task ID (e.g., TSK-XXXXXX)")
    workflow_id: str = Field(..., description="Associated workflow identifier")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    result: Optional[Dict[str, Any]] = Field(default=None, description="Task execution result payload")
    error_message: Optional[str] = Field(default=None, description="Error message if task failed")
    retry_count: int = Field(default=0, description="Number of times task execution has been retried")
    max_retries: int = Field(default=3, description="Maximum allowed retries before permanent failure")
    started_at: Optional[datetime] = Field(default=None, description="Execution start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Execution completion timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskResponse(TaskInDB):
    pass
