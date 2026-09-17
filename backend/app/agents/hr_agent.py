"""
agents/hr_agent.py — HR Specialized Agent.

Responsibilities:
- Employee Profile & Organization Verification ('HR Verification')
- Compliance Document Check & Missing Document Detection ('Document Verification')
"""

import uuid
from typing import Dict, Any, List
from datetime import datetime
from app.agents.base_agent import BaseAgent, AgentResult


class HRAgent(BaseAgent):
    """Specialized agent handling human resources validation and document compliance."""

    def __init__(self):
        super().__init__(
            agent_id="AGT-HR",
            name="HR Agent",
            agent_type="HR",
            description="Validates employee identity, organizational hierarchy, and completeness of submitted compliance documents."
        )

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """Dispatches task to the specific HR handler based on task_name."""
        task_name = task.get("task_name")
        
        if task_name == "HR Verification":
            return await self._verify_employee_profile(task, context)
        elif task_name == "Document Verification":
            return await self._verify_documents(task, context)
        else:
            return AgentResult(
                success=True,
                data={"message": f"HR Agent processed generic task '{task_name}'"},
                metadata={"agent": self.name}
            )

    async def _verify_employee_profile(self, task: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Validates core employee information: name, designation, department, and manager.
        """
        employee = context.get("employee", {})
        emp_name = employee.get("employee_name")
        emp_id = employee.get("employee_id")
        dept = employee.get("department")
        manager = employee.get("manager")

        if not emp_name or not dept or not manager:
            return AgentResult(
                success=False,
                error="Employee profile is incomplete: Missing name, department, or manager.",
                data={"employee_id": emp_id}
            )

        ref_id = f"HR-VFY-{uuid.uuid4().hex[:6].upper()}"
        return AgentResult(
            success=True,
            data={
                "verification_status": "VERIFIED",
                "verification_ref_id": ref_id,
                "employee_id": emp_id,
                "employee_name": emp_name,
                "department": dept,
                "reporting_manager": manager,
                "background_check": "CLEARED",
                "verified_at": datetime.utcnow().isoformat()
            },
            metadata={"agent": self.name, "handler": "verify_employee_profile"}
        )

    async def _verify_documents(self, task: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Inspects submitted document checklist.
        Mandatory documents: id_proof_submitted, address_proof_submitted.
        """
        employee = context.get("employee", {})
        emp_id = employee.get("employee_id")
        docs = employee.get("documents", {})

        missing_docs: List[str] = []
        if not docs.get("id_proof_submitted"):
            missing_docs.append("National ID / Passport Proof")
        if not docs.get("address_proof_submitted"):
            missing_docs.append("Permanent Address Proof")

        if missing_docs:
            return AgentResult(
                success=False,
                error=f"Document verification failed. Missing required documents: {', '.join(missing_docs)}",
                data={
                    "compliance_status": "INCOMPLETE",
                    "employee_id": emp_id,
                    "missing_documents": missing_docs,
                    "action_required": "Please upload missing identification documents."
                },
                metadata={"agent": self.name, "handler": "verify_documents"}
            )

        compliance_token = f"DOC-PASS-{uuid.uuid4().hex[:6].upper()}"
        return AgentResult(
            success=True,
            data={
                "compliance_status": "COMPLIANT",
                "compliance_token": compliance_token,
                "employee_id": emp_id,
                "verified_documents": [
                    "National ID / Passport Proof",
                    "Permanent Address Proof",
                    "Educational Certificates" if docs.get("education_certs_submitted") else None,
                    "Bank Account Details" if docs.get("bank_details_submitted") else None
                ],
                "verified_at": datetime.utcnow().isoformat()
            },
            metadata={"agent": self.name, "handler": "verify_documents"}
        )


# Singleton HR Agent instance
hr_agent = HRAgent()
