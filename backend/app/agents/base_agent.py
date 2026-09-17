"""
agents/base_agent.py — Base interface and contract for all agents.

Every specialized agent (HR, IT, Finance, Resource, Supervisor) inherits
from BaseAgent and implements the `execute` method.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentResult(BaseModel):
    """
    Standardized result contract returned by every agent.
    Agents NEVER write to the DB directly; they return this structured payload.
    """
    success: bool = Field(..., description="Whether the task succeeded")
    data: Dict[str, Any] = Field(default_factory=dict, description="Payload of simulated enterprise actions")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic and execution metadata")


class BaseAgent(ABC):
    """Abstract Base Class for all specialized agents."""

    def __init__(self, agent_id: str, name: str, agent_type: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.description = description

    @abstractmethod
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Executes the assigned task using the provided workflow/employee context.
        Must be implemented by each specialized sub-agent.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id='{self.agent_id}' name='{self.name}'>"
