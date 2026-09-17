"""
agents/it_agent.py — IT Specialized Agent.

Responsibilities:
- Corporate Email & SSO Identity Provisioning
- Department-Specific System Permission Assignment
- VPN & Internal Network Access Credential Generation
"""

import re
import uuid
from typing import Dict, Any, List
from datetime import datetime
from app.agents.base_agent import BaseAgent, AgentResult

# Department-tailored enterprise system access matrix
DEPARTMENT_PERMISSIONS_MATRIX: Dict[str, List[str]] = {
    "engineering": [
        "GitHub Enterprise (Write)",
        "AWS Cloud Development Environment",
        "Jira & Confluence Core Access",
        "Slack Pro Developer Channels",
        "Docker Hub Enterprise"
    ],
    "finance": [
        "NetSuite ERP",
        "QuickBooks Enterprise",
        "Expensify Payroll Portal",
        "Tableau Financial Analytics",
        "Slack Pro General"
    ],
    "operations": [
        "ServiceNow Enterprise ITSM",
        "SAP Cloud ERP",
        "Salesforce CRM Operations",
        "DocuSign Corporate",
        "Slack Pro General"
    ],
    "hr": [
        "Workday HCM Portal",
        "BambooHR HRIS",
        "Greenhouse Recruiting ATS",
        "DocuSign Corporate",
        "Slack Pro General"
    ],
    "forensics": [
        "Federal Digital Evidence Vault",
        "Secure Forensic Analysis Cloud",
        "Encrypted Terminal Access",
        "Case Management Database",
        "Slack Pro Secure"
    ]
}

DEFAULT_PERMISSIONS = [
    "Google Workspace Enterprise (Email, Docs, Drive)",
    "Slack Pro General Channels",
    "Internal Corporate Wiki (Confluence)",
    "Zoom Corporate Pro"
]


def _format_corporate_email(employee_name: str) -> str:
    """Sanitizes employee name into standard corporate email format."""
    clean_name = re.sub(r"[^a-zA-Z0-9\s]", "", employee_name).strip().lower()
    parts = clean_name.split()
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[-1]}@company.internal"
    return f"{clean_name}@company.internal"


class ITAgent(BaseAgent):
    """Specialized agent responsible for provisioning IT infrastructure and access permissions."""

    def __init__(self):
        super().__init__(
            agent_id="AGT-IT",
            name="IT Agent",
            agent_type="IT",
            description="Provisions corporate email, system permissions, single sign-on (SSO) credentials, and VPN access records."
        )

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """Dispatches IT tasks based on task_name."""
        task_name = task.get("task_name")
        if task_name == "IT Account Setup":
            return await self._setup_it_account(task, context)

        return AgentResult(
            success=True,
            data={"message": f"IT Agent processed generic task '{task_name}'"},
            metadata={"agent": self.name}
        )

    async def _setup_it_account(self, task: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Creates corporate email, assigns SSO ID, allocates department permissions,
        and generates VPN access credentials.
        """
        employee = context.get("employee", {})
        emp_name = employee.get("employee_name", "User")
        emp_id = employee.get("employee_id", "EMP-UNKNOWN")
        dept = employee.get("department", "general").strip().lower()
        designation = employee.get("designation", "Employee")

        # 1. Generate Corporate Email & SSO
        corporate_email = _format_corporate_email(emp_name)
        sso_id = f"SSO-USR-{uuid.uuid4().hex[:6].upper()}"

        # 2. Determine System Permissions from Department Matrix
        assigned_permissions = DEPARTMENT_PERMISSIONS_MATRIX.get(dept, DEFAULT_PERMISSIONS)

        # 3. Generate VPN Token
        vpn_token = f"VPN-PASS-{uuid.uuid4().hex[:6].upper()}"

        result_payload = {
            "it_setup_status": "PROVISIONED",
            "employee_id": emp_id,
            "employee_name": emp_name,
            "corporate_email": corporate_email,
            "sso_user_id": sso_id,
            "assigned_systems": assigned_permissions,
            "vpn_credentials": {
                "gateway": "vpn-gateway-us-east.corp.internal",
                "vpn_token": vpn_token,
                "status": "ACTIVE"
            },
            "security_clearance": "TIER-1 (STANDARD)",
            "provisioned_at": datetime.utcnow().isoformat()
        }

        return AgentResult(
            success=True,
            data=result_payload,
            metadata={"agent": self.name, "handler": "setup_it_account"}
        )


# Singleton IT Agent instance
it_agent = ITAgent()
