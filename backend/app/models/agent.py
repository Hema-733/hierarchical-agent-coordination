"""
models/agent.py — Pydantic models for Agent metadata.

Represents the specialized AI and rule agents registered in the framework.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    IDLE = "IDLE"
    BUSY = "BUSY"
    ERROR = "ERROR"


class AgentType(str, Enum):
    SUPERVISOR = "SUPERVISOR"
    HR = "HR"
    IT = "IT"
    FINANCE = "FINANCE"
    RESOURCE = "RESOURCE"


class AgentBase(BaseModel):
    agent_id: str = Field(..., description="Unique agent identifier (e.g., AGT-SUPERVISOR)")
    agent_name: str = Field(..., description="Display name of the agent")
    agent_type: AgentType = Field(..., description="Functional specialization")
    description: str = Field(..., description="Description of the agent's role and capabilities")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="Current operational status")


class AgentResponse(AgentBase):
    pass
