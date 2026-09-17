"""
api/agents.py — API Router for Agent Roster.

Provides endpoints to inspect all registered AI and system agents.
"""

from typing import List
from fastapi import APIRouter
from app.models.agent import AgentResponse
from app.db.repositories import agent_repo

router = APIRouter()


@router.get(
    "/",
    response_model=List[AgentResponse],
    summary="List all registered agents"
)
async def list_registered_agents():
    """Returns the list of all system agents and their current statuses."""
    agents = await agent_repo.list_agents()
    return [AgentResponse(**a) for a in agents]
