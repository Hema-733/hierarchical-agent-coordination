"""
api/onboarding.py — API Router for Employee Onboarding.

Provides endpoints for:
- Initiating employee onboarding
- Fetching registered employees
"""

from typing import List
from fastapi import APIRouter, status
from app.models.employee import EmployeeCreate, EmployeeResponse, OnboardingInitiationResponse
from app.services import onboarding_service

router = APIRouter()


@router.post(
    "/",
    response_model=OnboardingInitiationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new employee and initialize onboarding workflow",
    description="Validates employee data, generates IDs, saves employee record, and instantiates the workflow with 6 dependency-aware tasks."
)
async def create_employee_onboarding(employee_in: EmployeeCreate):
    """
    Submits a new employee profile to begin onboarding.
    """
    return await onboarding_service.register_new_employee(employee_in)


@router.get(
    "/employees/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get employee details by ID"
)
async def get_employee(employee_id: str):
    """
    Returns the details of a registered employee.
    """
    return await onboarding_service.fetch_employee(employee_id)


@router.get(
    "/employees",
    response_model=List[EmployeeResponse],
    summary="List all registered employees"
)
async def list_employees(skip: int = 0, limit: int = 50):
    """
    Returns a paginated list of all employees in the system.
    """
    from app.db.repositories import employee_repo
    employees = await employee_repo.list_employees(skip=skip, limit=limit)
    return [EmployeeResponse(**emp) for emp in employees]
