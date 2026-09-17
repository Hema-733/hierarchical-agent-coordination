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
