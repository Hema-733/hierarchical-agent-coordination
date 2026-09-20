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


async def update_employee_documents(
    employee_id: str,
    documents_update: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Updates document status and verification records for an employee.
    Safely merges document items and keeps legacy boolean flags in sync.
    """
    collection = _get_collection()
    existing = await collection.find_one({"employee_id": employee_id}, {"_id": 0})
    if not existing:
        return None

    current_docs = existing.get("documents", {})
    # Normalize current_docs if it was a plain dict of booleans
    for doc_key in ["id_proof", "address_proof", "bank_details", "education_certs"]:
        if doc_key not in current_docs and f"{doc_key}_submitted" in current_docs:
            is_sub = bool(current_docs[f"{doc_key}_submitted"])
            current_docs[doc_key] = {
                "submitted": is_sub,
                "status": "SUBMITTED" if is_sub else "MISSING",
                "document_name": f"{doc_key}.pdf"
            }

    # Apply updates
    for k, v in documents_update.items():
        if isinstance(v, dict) and isinstance(current_docs.get(k), dict):
            current_docs[k].update(v)
        else:
            current_docs[k] = v

    # Ensure boolean flags stay in sync
    for doc_key in ["id_proof", "address_proof", "bank_details", "education_certs"]:
        doc_obj = current_docs.get(doc_key)
        if isinstance(doc_obj, dict):
            is_sub = doc_obj.get("submitted", False) or doc_obj.get("status") in [
                "SUBMITTED", "UNDER_REVIEW", "VERIFIED"
            ]
            current_docs[f"{doc_key}_submitted"] = is_sub

    now = datetime.utcnow()
    updated = await collection.find_one_and_update(
        {"employee_id": employee_id},
        {
            "$set": {
                "documents": current_docs,
                "updated_at": now
            }
        },
        projection={"_id": 0},
        return_document=True
    )
    return updated
