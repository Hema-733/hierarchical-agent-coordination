"""
models/workflow.py — Pydantic models for Workflows.

Tracks overall onboarding workflow state and aggregate progress.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.task import TaskResponse


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WorkflowType(str, Enum):
    EMPLOYEE_ONBOARDING = "EMPLOYEE_ONBOARDING"


class WorkflowBase(BaseModel):
    employee_id: str = Field(..., description="ID of the onboarded employee")
    workflow_type: WorkflowType = Field(default=WorkflowType.EMPLOYEE_ONBOARDING)


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowInDB(WorkflowBase):
    workflow_id: str = Field(..., description="Unique generated workflow ID (e.g., WF-XXXXXX)")
    overall_status: WorkflowStatus = Field(default=WorkflowStatus.PENDING)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom workflow execution metadata")
    paused_at: Optional[datetime] = Field(default=None, description="Timestamp when the workflow was last paused")
    paused_reason: Optional[str] = Field(default=None, description="Human-readable reason for pausing")
    resumed_at: Optional[datetime] = Field(default=None, description="Timestamp when the workflow was last resumed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowResponse(WorkflowInDB):
    tasks: Optional[List[TaskResponse]] = Field(default=None, description="Optional embedded task list")
