"""
db/repositories/employee_repo.py — MongoDB CRUD operations for Employee records.

Follows the Repository pattern to isolate all database queries from business logic.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.connection import get_database


def _get_collection():
    """Helper to access the 'employees' collection."""
    db = get_database()
    return db["employees"]


async def create_employee(employee_doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inserts a new employee document into MongoDB.
    Returns the created document (excluding MongoDB's internal _id for clean API serialization).
    """
    collection = _get_collection()
    doc_to_insert = dict(employee_doc)
    doc_to_insert["created_at"] = doc_to_insert.get("created_at", datetime.utcnow())
    doc_to_insert["updated_at"] = doc_to_insert.get("updated_at", datetime.utcnow())
    
    await collection.insert_one(doc_to_insert)
    # Remove Mongo's internal ObjectId before returning
    doc_to_insert.pop("_id", None)
    return doc_to_insert


async def get_employee_by_id(employee_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves an employee by their unique employee_id.
    """
    collection = _get_collection()
    doc = await collection.find_one({"employee_id": employee_id}, {"_id": 0})
    return doc


async def get_employee_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves an employee by their email address.
    """
    collection = _get_collection()
    doc = await collection.find_one({"email": email}, {"_id": 0})
    return doc


async def list_employees(skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Lists employees with pagination.
    """
    collection = _get_collection()
    cursor = collection.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def update_employee_documents(employee_id: str, documents: Dict[str, bool]) -> Optional[Dict[str, Any]]:
    """
    Updates document status checklist for an employee.
    """
    collection = _get_collection()
    updated = await collection.find_one_and_update(
        {"employee_id": employee_id},
        {
            "$set": {
                "documents": documents,
                "updated_at": datetime.utcnow()
            }
        },
        projection={"_id": 0},
        return_document=True
    )
    return updated
