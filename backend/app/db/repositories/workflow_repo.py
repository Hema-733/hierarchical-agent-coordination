"""
db/repositories/workflow_repo.py — MongoDB CRUD operations for Workflows.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.connection import get_database


def _get_collection():
    db = get_database()
    return db["workflows"]


async def create_workflow(workflow_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Inserts a new workflow record."""
    collection = _get_collection()
    doc = dict(workflow_doc)
    doc["created_at"] = doc.get("created_at", datetime.utcnow())
    doc["updated_at"] = doc.get("updated_at", datetime.utcnow())
    await collection.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def get_workflow_by_id(workflow_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single workflow by ID."""
    collection = _get_collection()
    return await collection.find_one({"workflow_id": workflow_id}, {"_id": 0})


async def get_workflows_by_employee_id(employee_id: str) -> List[Dict[str, Any]]:
    """Retrieves all workflows for a given employee."""
    collection = _get_collection()
    cursor = collection.find({"employee_id": employee_id}, {"_id": 0}).sort("created_at", -1)
    return await cursor.to_list(length=50)


async def list_workflows(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lists workflows with optional status filtering and pagination."""
    collection = _get_collection()
    query = {}
    if status:
        query["overall_status"] = status
    cursor = collection.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def update_workflow_status(
    workflow_id: str,
    overall_status: str,
    metadata_patch: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Updates overall_status and metadata for a workflow."""
    collection = _get_collection()
    update_fields: Dict[str, Any] = {
        "overall_status": overall_status,
        "updated_at": datetime.utcnow()
    }
    
    update_op: Dict[str, Any] = {"$set": update_fields}
    if metadata_patch:
        for k, v in metadata_patch.items():
            update_op["$set"][f"metadata.{k}"] = v

    return await collection.find_one_and_update(
        {"workflow_id": workflow_id},
        update_op,
        projection={"_id": 0},
        return_document=True
    )
