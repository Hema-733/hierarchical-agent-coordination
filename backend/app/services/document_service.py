"""
services/document_service.py — Centralized document verification requirements and validation rules.

Enforces business logic for:
- Mapping document types to required pipeline stages
- Validating document compliance before task execution
- Updating and auditing document verification records
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from app.models.employee import DocumentReviewStatus


DOCUMENT_DEFINITIONS = {
    "id_proof": {
        "key": "id_proof",
        "label": "National ID / Passport",
        "required_for_task": "Document Verification",
        "agent": "HR Agent",
        "mandatory": True,
        "description": "Government-issued identity verification",
    },
    "address_proof": {
        "key": "address_proof",
        "label": "Proof of Address",
        "required_for_task": "Document Verification",
        "agent": "HR Agent",
        "mandatory": True,
        "description": "Utility bill, bank statement, or permanent residency proof",
    },
    "bank_details": {
        "key": "bank_details",
        "label": "Bank Account Details",
        "required_for_task": "Payroll Setup",
        "agent": "Finance Agent",
        "mandatory": True,
        "description": "Direct deposit account and routing details for compensation",
    },
    "education_certs": {
        "key": "education_certs",
        "label": "Education Certificates",
        "required_for_task": "Document Verification",
        "agent": "HR Agent",
        "mandatory": False,
        "description": "Academic degree, diploma, or professional accreditation",
    },
}


def is_document_approved(doc_data: Any) -> bool:
    """Checks if a document is considered verified or approved."""
    if not isinstance(doc_data, dict):
        return bool(doc_data)
    status = doc_data.get("status")
    return status == DocumentReviewStatus.VERIFIED.value


def is_document_acceptable_for_automated_check(doc_data: Any) -> bool:
    """
    Checks if a document has been submitted and is not rejected/missing.
    Automated check can proceed if document was submitted or verified.
    """
    if not isinstance(doc_data, dict):
        return bool(doc_data)
    status = doc_data.get("status")
    submitted = doc_data.get("submitted", False)
    if status == DocumentReviewStatus.REJECTED.value:
        return False
    if status in [
        DocumentReviewStatus.VERIFIED.value,
        DocumentReviewStatus.SUBMITTED.value,
        DocumentReviewStatus.UNDER_REVIEW.value,
    ]:
        return True
    return bool(submitted)


def validate_task_document_requirements(
    task_name: str, documents: Dict[str, Any]
) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
    """
    Validates whether all mandatory documents for a given task meet requirements.
    Returns:
        (is_compliant, list_of_deficient_docs, error_message)
    """
    deficient: List[Dict[str, Any]] = []

    for key, spec in DOCUMENT_DEFINITIONS.items():
        if spec["required_for_task"] != task_name or not spec["mandatory"]:
            continue

        doc = documents.get(key)
        # Fallback to legacy boolean if dict not yet instantiated
        if doc is None:
            legacy_bool = documents.get(f"{key}_submitted", False)
            doc = {
                "submitted": legacy_bool,
                "status": (
                    DocumentReviewStatus.SUBMITTED.value
                    if legacy_bool
                    else DocumentReviewStatus.MISSING.value
                ),
            }

        # Check document validity
        if not is_document_acceptable_for_automated_check(doc):
            curr_status = doc.get("status", DocumentReviewStatus.MISSING.value) if isinstance(doc, dict) else "MISSING"
            rejection_note = doc.get("review_note") if isinstance(doc, dict) else None
            deficient.append(
                {
                    "key": key,
                    "label": spec["label"],
                    "status": curr_status,
                    "review_note": rejection_note,
                    "reason": f"{spec['label']} is {curr_status.lower()}",
                }
            )

    if not deficient:
        return True, [], None

    labels = [d["label"] for d in deficient]
    reasons = [
        f"{d['label']} ({d['status']}{': ' + d['review_note'] if d['review_note'] else ''})"
        for d in deficient
    ]
    error_msg = f"{', '.join(labels)} required for {task_name}: {'; '.join(reasons)}."
    return False, deficient, error_msg
