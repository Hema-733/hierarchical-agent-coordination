"""
db/repositories/agent_repo.py — MongoDB operations for Agent metadata.
"""

from typing import List, Optional, Dict, Any
from app.db.connection import get_database


def _get_collection():
    db = get_database()
    return db["agents"]


async def upsert_agent(agent_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Inserts or updates an agent specification by agent_id."""
    collection = _get_collection()
    agent_id = agent_doc["agent_id"]
    await collection.update_one(
        {"agent_id": agent_id},
        {"$set": agent_doc},
        upsert=True
    )
    doc = await collection.find_one({"agent_id": agent_id}, {"_id": 0})
    return doc


async def list_agents() -> List[Dict[str, Any]]:
    """Lists all registered agents."""
    collection = _get_collection()
    cursor = collection.find({}, {"_id": 0}).sort("agent_id", 1)
    return await cursor.to_list(length=100)


async def get_agent_by_id(agent_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves an agent by ID."""
    collection = _get_collection()
    return await collection.find_one({"agent_id": agent_id}, {"_id": 0})
