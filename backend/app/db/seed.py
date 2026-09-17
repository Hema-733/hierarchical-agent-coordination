"""
db/seed.py — Seeds initial Agent records into MongoDB on application startup.
"""

from app.db.repositories.agent_repo import upsert_agent

DEFAULT_AGENTS = [
    {
        "agent_id": "AGT-SUPERVISOR",
        "agent_name": "Supervisor Agent",
        "agent_type": "SUPERVISOR",
        "description": "Main orchestrator responsible for workflow decomposition, task dispatching, dependency tracking, failure handling, and completion checks.",
        "status": "IDLE"
    },
    {
        "agent_id": "AGT-HR",
        "agent_name": "HR Agent",
        "agent_type": "HR",
        "description": "Validates employee identity, background records, and completeness of submitted compliance documents.",
        "status": "IDLE"
    },
    {
        "agent_id": "AGT-IT",
        "agent_name": "IT Agent",
        "agent_type": "IT",
        "description": "Provisions corporate email, system permissions, single sign-on (SSO) credentials, and VPN access records.",
        "status": "IDLE"
    },
    {
        "agent_id": "AGT-FINANCE",
        "agent_name": "Finance Agent",
        "agent_type": "FINANCE",
        "description": "Verifies bank account details, configures tax withholdings, and registers the employee in payroll.",
        "status": "IDLE"
    },
    {
        "agent_id": "AGT-RESOURCE",
        "agent_name": "Resource / Admin Agent",
        "agent_type": "RESOURCE",
        "description": "Checks hardware inventory, assigns designated laptops/monitors, and allocates workspace desks and access badges.",
        "status": "IDLE"
    }
]


async def seed_agents() -> None:
    """Inserts or updates the 5 standard agents in MongoDB."""
    for agent_data in DEFAULT_AGENTS:
        await upsert_agent(agent_data)
    print(f"[Seed] Successfully seeded {len(DEFAULT_AGENTS)} system agents.")
