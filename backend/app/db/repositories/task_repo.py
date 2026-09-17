"""
db/repositories/task_repo.py — MongoDB CRUD operations for Tasks.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.connection import get_database


def _get_collection():
    db = get_database()
    return db["tasks"]


async def create_tasks_batch(task_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Inserts multiple task records for a workflow."""
    if not task_docs:
        return []
    collection = _get_collection()
    docs = []
    now = datetime.utcnow()
    for t in task_docs:
        d = dict(t)
        d["created_at"] = d.get("created_at", now)
        d["updated_at"] = d.get("updated_at", now)
        docs.append(d)
    
    await collection.insert_many(docs)
    for d in docs:
        d.pop("_id", None)
    return docs


async def create_task(task_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Inserts a single task."""
    collection = _get_collection()
    doc = dict(task_doc)
    doc["created_at"] = doc.get("created_at", datetime.utcnow())
    doc["updated_at"] = doc.get("updated_at", datetime.utcnow())
    await collection.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single task by its task_id."""
    collection = _get_collection()
    return await collection.find_one({"task_id": task_id}, {"_id": 0})


async def get_tasks_by_workflow(workflow_id: str) -> List[Dict[str, Any]]:
    """Retrieves all tasks belonging to a specific workflow."""
    collection = _get_collection()
    cursor = collection.find({"workflow_id": workflow_id}, {"_id": 0}).sort("created_at", 1)
    return await cursor.to_list(length=100)


async def get_task_by_workflow_and_name(workflow_id: str, task_name: str) -> Optional[Dict[str, Any]]:
    """Retrieves a task by workflow_id and task_name."""
    collection = _get_collection()
    return await collection.find_one(
        {"workflow_id": workflow_id, "task_name": task_name},
        {"_id": 0}
    )


async def update_task_status(
    task_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    started: bool = False,
    completed: bool = False
) -> Optional[Dict[str, Any]]:
    """Updates status, execution timestamps, results, or error messages for a task."""
    collection = _get_collection()
    now = datetime.utcnow()
    set_fields: Dict[str, Any] = {
        "status": status,
        "updated_at": now
    }
    
    if result is not None:
        set_fields["result"] = result
    if error_message is not None:
        set_fields["error_message"] = error_message
    if started:
        set_fields["started_at"] = now
    if completed:
        set_fields["completed_at"] = now

    return await collection.find_one_and_update(
        {"task_id": task_id},
        {"$set": set_fields},
        projection={"_id": 0},
        return_document=True
    )


async def increment_task_retry(task_id: str) -> Optional[Dict[str, Any]]:
    """Increments retry counter and sets status to READY."""
    collection = _get_collection()
    return await collection.find_one_and_update(
        {"task_id": task_id},
        {
            "$inc": {"retry_count": 1},
            "$set": {
                "status": "READY",
                "error_message": None,
                "updated_at": datetime.utcnow()
            }
        },
        projection={"_id": 0},
        return_document=True
    )
