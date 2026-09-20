"""
models/employee.py — Pydantic models for Employee data validation and Document Verification.

Defines schemas for:
- Structured document verification lifecycle (MISSING, SUBMITTED, UNDER_REVIEW, VERIFIED, REJECTED)
- Backward-compatible boolean flags
- Creating an employee (incoming request from form)
- Updating employee documents (PATCH /onboarding/employees/{id}/documents)
- Employee DB representation and API responses
"""

from enum import Enum
from datetime import datetime, date
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, EmailStr, model_validator
from app.models.workflow import WorkflowResponse


class DocumentReviewStatus(str, Enum):
    MISSING = "MISSING"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class DocumentItem(BaseModel):
    """Metadata and verification lifecycle state for an individual document."""
    submitted: bool = Field(default=False, description="Whether document info has been submitted")
    status: DocumentReviewStatus = Field(default=DocumentReviewStatus.MISSING, description="Verification review status")
    document_name: Optional[str] = Field(default=None, description="Simulated document attachment name")
    verified_by: Optional[str] = Field(default=None, description="Identifier of verifier (e.g., HR, System)")
    verified_at: Optional[datetime] = Field(default=None, description="Timestamp of verification")
    review_note: Optional[str] = Field(default=None, description="Review feedback or rejection notes")


class DocumentStatus(BaseModel):
    """
    Tracks document submission and review statuses.
    Maintains full backward compatibility with legacy boolean submission flags.
    """
    # Backward-compatible booleans
    id_proof_submitted: bool = Field(default=False, description="Legacy flag: National ID submitted")
    address_proof_submitted: bool = Field(default=False, description="Legacy flag: Address proof submitted")
    bank_details_submitted: bool = Field(default=False, description="Legacy flag: Bank details submitted")
    education_certs_submitted: bool = Field(default=False, description="Legacy flag: Education certificates submitted")

    # Structured document review records
    id_proof: DocumentItem = Field(default_factory=lambda: DocumentItem(document_name="National_ID_Passport.pdf"))
    address_proof: DocumentItem = Field(default_factory=lambda: DocumentItem(document_name="Proof_of_Address.pdf"))
    bank_details: DocumentItem = Field(default_factory=lambda: DocumentItem(document_name="Bank_Account_Details.pdf"))
    education_certs: DocumentItem = Field(default_factory=lambda: DocumentItem(document_name="Education_Certificates.pdf"))

    @model_validator(mode="before")
    @classmethod
    def sync_and_normalize(cls, data: Any) -> Any:
        """
        Normalizes existing boolean records and ensures consistency between
        legacy boolean flags and structured DocumentItem models.
        """
        if not isinstance(data, dict):
            return data

        mapping = [
            ("id_proof", "id_proof_submitted", "National_ID_Passport.pdf"),
            ("address_proof", "address_proof_submitted", "Proof_of_Address.pdf"),
            ("bank_details", "bank_details_submitted", "Bank_Account_Details.pdf"),
            ("education_certs", "education_certs_submitted", "Education_Certificates.pdf"),
        ]

        normalized = dict(data)

        for doc_key, bool_key, default_filename in mapping:
            doc_data = normalized.get(doc_key)
            bool_val = normalized.get(bool_key)

            if isinstance(doc_data, dict):
                # If rich doc object exists, extract submission and sync boolean
                curr_status = doc_data.get("status", DocumentReviewStatus.MISSING.value)
                is_sub = (
                    doc_data.get("submitted", False)
                    or curr_status in [
                        DocumentReviewStatus.SUBMITTED.value,
                        DocumentReviewStatus.UNDER_REVIEW.value,
                        DocumentReviewStatus.VERIFIED.value,
                    ]
                )
                doc_data["submitted"] = is_sub
                if not doc_data.get("document_name"):
                    doc_data["document_name"] = default_filename
                normalized[bool_key] = is_sub
            elif doc_data is not None:
                # If already a model instance
                normalized[bool_key] = bool(getattr(doc_data, "submitted", False))
            elif bool_val is not None:
                # If only legacy boolean flag exists (e.g. older DB record or simpler form submit)
                is_sub = bool(bool_val)
                doc_status = (
                    DocumentReviewStatus.SUBMITTED.value
                    if is_sub
                    else DocumentReviewStatus.MISSING.value
                )
                normalized[doc_key] = {
                    "submitted": is_sub,
                    "status": doc_status,
                    "document_name": default_filename,
                    "verified_by": "Automated Intake" if is_sub else None,
                    "verified_at": datetime.utcnow().isoformat() if is_sub else None,
                    "review_note": None,
                }
            else:
                normalized[doc_key] = {
                    "submitted": False,
                    "status": DocumentReviewStatus.MISSING.value,
                    "document_name": default_filename,
                }
                normalized[bool_key] = False

        return normalized


class DocumentUpdateItem(BaseModel):
    """Schema for updating an individual document."""
    submitted: Optional[bool] = None
    status: Optional[DocumentReviewStatus] = None
    document_name: Optional[str] = None
    verified_by: Optional[str] = None
    review_note: Optional[str] = None


class EmployeeDocumentsUpdateRequest(BaseModel):
    """Schema for PATCH /onboarding/employees/{id}/documents"""
    id_proof: Optional[DocumentUpdateItem] = None
    address_proof: Optional[DocumentUpdateItem] = None
    bank_details: Optional[DocumentUpdateItem] = None
    education_certs: Optional[DocumentUpdateItem] = None
    # Optional workflow ID to automatically unblock and resume
    workflow_id: Optional[str] = None
    auto_resume: Optional[bool] = True


class EmployeeBase(BaseModel):
    """Common fields shared across Employee models."""
    employee_name: str = Field(..., min_length=2, max_length=100, description="Full name of employee")
    email: EmailStr = Field(..., description="Corporate or personal email address")
    phone: str = Field(..., min_length=10, max_length=20, description="Contact phone number")
    department: str = Field(..., min_length=2, max_length=50, description="Assigned department (e.g., Engineering, HR)")
    designation: str = Field(..., min_length=2, max_length=50, description="Job title / role")
    joining_date: date = Field(..., description="Date of joining")
    manager: str = Field(..., min_length=2, max_length=100, description="Reporting manager's name")
    documents: DocumentStatus = Field(default_factory=DocumentStatus, description="Document checklist and verification lifecycle")


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
