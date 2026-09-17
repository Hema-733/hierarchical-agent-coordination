"""
models/employee.py — Pydantic models for Employee data validation.

Defines schemas for:
- Creating an employee (incoming request from form)
- Employee DB representation
- Employee response returned to clients
"""

from datetime import datetime, date
from typing import Optional, Any
from pydantic import BaseModel, Field, EmailStr
from app.models.workflow import WorkflowResponse


class DocumentStatus(BaseModel):
    """Tracks document submission statuses without requiring actual file uploads."""
    id_proof_submitted: bool = Field(default=False, description="National ID / Passport submitted")
    address_proof_submitted: bool = Field(default=False, description="Utility bill / Address proof submitted")
    bank_details_submitted: bool = Field(default=False, description="Bank account details submitted for payroll")
    education_certs_submitted: bool = Field(default=False, description="Educational certificates submitted")


class EmployeeBase(BaseModel):
    """Common fields shared across Employee models."""
    employee_name: str = Field(..., min_length=2, max_length=100, description="Full name of employee")
    email: EmailStr = Field(..., description="Corporate or personal email address")
    phone: str = Field(..., min_length=10, max_length=20, description="Contact phone number")
    department: str = Field(..., min_length=2, max_length=50, description="Assigned department (e.g., Engineering, HR)")
    designation: str = Field(..., min_length=2, max_length=50, description="Job title / role")
    joining_date: date = Field(..., description="Date of joining")
    manager: str = Field(..., min_length=2, max_length=100, description="Reporting manager's name")
    documents: DocumentStatus = Field(default_factory=DocumentStatus, description="Document checklist status")


class EmployeeCreate(EmployeeBase):
    """Schema for creating a new employee via POST /onboarding/"""
    pass


class EmployeeInDB(EmployeeBase):
    """Schema stored internally in MongoDB."""
    employee_id: str = Field(..., description="Unique generated Employee ID (e.g. EMP-2026-XXXX)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Record last updated timestamp")


class EmployeeResponse(EmployeeInDB):
    """Schema returned in API responses."""
    pass


class OnboardingInitiationResponse(BaseModel):
    """Returned when a new onboarding request is submitted."""
    employee: EmployeeResponse
    workflow: WorkflowResponse
