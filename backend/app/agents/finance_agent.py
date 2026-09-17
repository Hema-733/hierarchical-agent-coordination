"""
agents/finance_agent.py — Finance Specialized Agent.

Responsibilities:
- Bank Account Detail Validation ('Payroll Setup')
- Payroll Record Creation with Tax Configuration
"""

import uuid
from typing import Dict, Any
from datetime import datetime
from app.agents.base_agent import BaseAgent, AgentResult

# Salary bands by designation (simulated)
SALARY_BAND_LOOKUP = {
    "intern": {"grade": "G1", "band": "INTERN", "range": "15000-25000"},
    "junior": {"grade": "G2", "band": "JUNIOR", "range": "25000-45000"},
    "engineer": {"grade": "G3", "band": "MID", "range": "45000-80000"},
    "senior": {"grade": "G4", "band": "SENIOR", "range": "80000-130000"},
    "lead": {"grade": "G5", "band": "LEAD", "range": "100000-160000"},
    "manager": {"grade": "G6", "band": "MANAGER", "range": "120000-200000"},
    "director": {"grade": "G7", "band": "DIRECTOR", "range": "180000-300000"},
}
DEFAULT_BAND = {"grade": "G3", "band": "MID", "range": "45000-80000"}


def _resolve_salary_band(designation: str) -> dict:
    designation_lower = designation.strip().lower()
    for key, band in SALARY_BAND_LOOKUP.items():
        if key in designation_lower:
            return band
    return DEFAULT_BAND


class FinanceAgent(BaseAgent):
    """Specialized agent responsible for payroll registration and compensation setup."""

    def __init__(self):
        super().__init__(
            agent_id="AGT-FINANCE",
            name="Finance Agent",
            agent_type="FINANCE",
            description="Verifies bank account details, configures tax withholdings, and registers the employee in payroll."
        )

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """Dispatches finance tasks based on task_name."""
        task_name = task.get("task_name")
        if task_name == "Payroll Setup":
            return await self._setup_payroll(task, context)
        return AgentResult(
            success=True,
            data={"message": f"Finance Agent processed generic task '{task_name}'"},
            metadata={"agent": self.name}
        )

    async def _setup_payroll(self, task: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Validates bank account details and creates a payroll record with tax configuration.
        """
        employee = context.get("employee", {})
        emp_id = employee.get("employee_id")
        emp_name = employee.get("employee_name")
        designation = employee.get("designation", "")
        documents = employee.get("documents", {})

        # Validate bank details submitted
        if not documents.get("bank_details_submitted", False):
            return AgentResult(
                success=False,
                error="Payroll setup failed: Bank account details have not been submitted by the employee.",
                data={
                    "payroll_status": "BLOCKED",
                    "employee_id": emp_id,
                    "missing": "bank_details_submitted"
                },
                metadata={"agent": self.name}
            )

        salary_band = _resolve_salary_band(designation)
        payroll_id = f"PAY-{uuid.uuid4().hex[:6].upper()}"
        tax_ref = f"TAX-{uuid.uuid4().hex[:6].upper()}"

        return AgentResult(
            success=True,
            data={
                "payroll_status": "REGISTERED",
                "payroll_id": payroll_id,
                "employee_id": emp_id,
                "employee_name": emp_name,
                "designation": designation,
                "salary_grade": salary_band["grade"],
                "salary_band": salary_band["band"],
                "salary_range_usd": salary_band["range"],
                "pay_cycle": "MONTHLY",
                "payment_method": "DIRECT_DEPOSIT",
                "tax_configuration": {
                    "tax_ref_id": tax_ref,
                    "withholding_percentage": 22.5,
                    "tax_bracket": "STANDARD",
                    "pf_contribution": True
                },
                "first_payroll_date": "2026-11-01",
                "registered_at": datetime.utcnow().isoformat()
            },
            metadata={"agent": self.name, "handler": "setup_payroll"}
        )


# Singleton Finance Agent instance
finance_agent = FinanceAgent()
