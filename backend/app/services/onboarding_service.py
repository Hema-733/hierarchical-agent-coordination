"""
services/onboarding_service.py — Business logic for employee onboarding.

Handles:
- Generating unique Employee and Workflow IDs
- Checking for duplicates
- Persisting employee records
- Creating associated onboarding workflow and tasks
"""

import uuid
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.models.employee import EmployeeCreate, EmployeeResponse
from app.models.workflow import WorkflowResponse
from app.db.repositories import employee_repo
from app.services import workflow_service


def generate_employee_id() -> str:
    """Generates a human-friendly unique employee ID."""
    short_uuid = uuid.uuid4().hex[:6].upper()
    return f"EMP-{short_uuid}"


async def register_new_employee(employee_in: EmployeeCreate) -> Dict[str, Any]:
    """
    Validates business rules, registers a new employee record,
    and automatically spawns an onboarding workflow with initialized tasks.
    """
    # Check if an employee with this email already exists
    existing = await employee_repo.get_employee_by_email(employee_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An employee with email '{employee_in.email}' is already registered."
        )

    employee_dict = employee_in.model_dump()
    emp_id = generate_employee_id()
    employee_dict["employee_id"] = emp_id
    employee_dict["joining_date"] = str(employee_in.joining_date)

    saved_employee = await employee_repo.create_employee(employee_dict)
    
    # Initialize the onboarding workflow and task dependency graph
    workflow = await workflow_service.create_onboarding_workflow(emp_id)

    return {
        "employee": EmployeeResponse(**saved_employee),
        "workflow": workflow
    }


async def fetch_employee(employee_id: str) -> Optional[EmployeeResponse]:
    """Retrieves an employee record by employee_id."""
    emp = await employee_repo.get_employee_by_id(employee_id)
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{employee_id}' not found."
        )
    return EmployeeResponse(**emp)


async def update_employee_documents(
    employee_id: str,
    update_req: "EmployeeDocumentsUpdateRequest"
) -> EmployeeResponse:
    """
    Updates document metadata, verification status, and review notes.
    Optionally unblocks and resumes an associated paused workflow.
    """
    from datetime import datetime
    from app.services.event_broker import event_broker
    from app.db.repositories import workflow_repo
    from app.models.employee import DocumentReviewStatus

    emp = await employee_repo.get_employee_by_id(employee_id)
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{employee_id}' not found."
        )

    update_dict: Dict[str, Any] = {}
    verified_docs = []
    rejected_docs = []

    for doc_key in ["id_proof", "address_proof", "bank_details", "education_certs"]:
        item = getattr(update_req, doc_key, None)
        if item is not None:
            doc_patch: Dict[str, Any] = {}
            if item.status is not None:
                doc_patch["status"] = item.status.value
                if item.status == DocumentReviewStatus.VERIFIED:
                    verified_docs.append(doc_key)
                    doc_patch["verified_by"] = item.verified_by or "HR"
                    doc_patch["verified_at"] = datetime.utcnow()
                    doc_patch["submitted"] = True
                elif item.status == DocumentReviewStatus.REJECTED:
                    rejected_docs.append(doc_key)
                elif item.status in [DocumentReviewStatus.SUBMITTED, DocumentReviewStatus.UNDER_REVIEW]:
                    doc_patch["submitted"] = True
            if item.submitted is not None:
                doc_patch["submitted"] = item.submitted
            if item.document_name is not None:
                doc_patch["document_name"] = item.document_name
            if item.review_note is not None:
                doc_patch["review_note"] = item.review_note
            if item.verified_by is not None:
                doc_patch["verified_by"] = item.verified_by

            update_dict[doc_key] = doc_patch

    updated_emp = await employee_repo.update_employee_documents(employee_id, update_dict)
    if not updated_emp:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update employee documents."
        )

    wf_id = update_req.workflow_id
    if wf_id:
        if verified_docs:
            event_broker.publish(
                workflow_id=wf_id,
                event_type="DOCUMENT_VERIFIED",
                message=f"HR verified document(s): {', '.join(verified_docs)}.",
                status="RUNNING",
                data={"verified_documents": verified_docs, "employee_id": employee_id},
            )
        if rejected_docs:
            event_broker.publish(
                workflow_id=wf_id,
                event_type="DOCUMENT_REJECTED",
                message=f"HR rejected document(s): {', '.join(rejected_docs)}.",
                status="PAUSED",
                data={"rejected_documents": rejected_docs, "employee_id": employee_id},
            )
        event_broker.publish(
            workflow_id=wf_id,
            event_type="DOCUMENT_UPDATED",
            message=f"Employee document records updated for {employee_id}.",
            status="RUNNING",
            data={"updated_fields": list(update_dict.keys()), "employee_id": employee_id},
        )

        # If auto_resume is requested, documents were verified, and none were rejected:
        if update_req.auto_resume and verified_docs and not rejected_docs:
            wf = await workflow_repo.get_workflow_by_id(wf_id)
            if wf and wf.get("overall_status") == "PAUSED":
                from app.agents.supervisor_agent import supervisor_agent
                print(f"[OnboardingService] Verified document for PAUSED workflow '{wf_id}'. Resuming coordination...")
                await workflow_service.resume_workflow(wf_id)
                await supervisor_agent.run_workflow(wf_id)

    return EmployeeResponse(**updated_emp)
