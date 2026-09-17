"""
agents/resource_agent.py — Resource / Admin Specialized Agent.

Responsibilities:
- Hardware Inventory Check & Laptop Allocation ('Resource Allocation')
- Physical Workspace Assignment
- Corporate Access Badge Issuance
"""

import uuid
import random
from typing import Dict, Any, List
from datetime import datetime
from app.agents.base_agent import BaseAgent, AgentResult

# Simulated hardware inventory pool (department-specific recommendations)
HARDWARE_CATALOG = {
    "engineering": {
        "laptop": "MacBook Pro M3 (16GB RAM, 512GB SSD)",
        "monitor": "Dell UltraSharp 27\" 4K",
        "peripherals": ["Mechanical Keyboard", "Ergonomic Mouse", "USB-C Hub", "Noise-Cancelling Headset"]
    },
    "finance": {
        "laptop": "Lenovo ThinkPad X1 Carbon (16GB RAM, 256GB SSD)",
        "monitor": "Dell 24\" Full HD (Dual Setup)",
        "peripherals": ["Standard Keyboard", "Optical Mouse", "USB Hub", "Deskphone"]
    },
    "hr": {
        "laptop": "HP EliteBook 840 (8GB RAM, 256GB SSD)",
        "monitor": "HP 24\" Full HD",
        "peripherals": ["Standard Keyboard", "Optical Mouse", "Webcam Pro"]
    },
    "operations": {
        "laptop": "Dell Latitude 7420 (16GB RAM, 256GB SSD)",
        "monitor": "LG 24\" Full HD",
        "peripherals": ["Standard Keyboard", "Wireless Mouse", "USB Hub", "Barcode Scanner"]
    },
    "forensics": {
        "laptop": "ThinkPad X1 Extreme (32GB RAM, 1TB SSD, Encrypted)",
        "monitor": "Samsung 27\" 4K Curved (Privacy Filter)",
        "peripherals": ["Encrypted Keyboard", "Biometric Mouse", "Secure USB Hub", "Evidence Collection Kit"]
    }
}

DEFAULT_HARDWARE = {
    "laptop": "Dell Latitude 5520 (8GB RAM, 256GB SSD)",
    "monitor": "HP 22\" Full HD",
    "peripherals": ["Standard Keyboard", "Optical Mouse"]
}

# Simulated floor/desk pool
WORKSPACE_FLOORS = ["Floor 3", "Floor 4", "Floor 5", "Floor 6", "Floor 7"]
DESK_ZONES = ["Zone A", "Zone B", "Zone C", "Zone D"]


class ResourceAgent(BaseAgent):
    """Specialized agent responsible for physical resource allocation and workspace setup."""

    def __init__(self):
        super().__init__(
            agent_id="AGT-RESOURCE",
            name="Resource / Admin Agent",
            agent_type="RESOURCE",
            description="Checks hardware inventory, assigns designated laptops/monitors, and allocates workspace desks and access badges."
        )

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """Dispatches resource allocation tasks based on task_name."""
        task_name = task.get("task_name")
        if task_name == "Resource Allocation":
            return await self._allocate_resources(task, context)
        return AgentResult(
            success=True,
            data={"message": f"Resource Agent processed generic task '{task_name}'"},
            metadata={"agent": self.name}
        )

    async def _allocate_resources(self, task: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Assigns hardware, workspace desk, and corporate access badge.
        Generates an asset record and access badge number.
        """
        employee = context.get("employee", {})
        emp_id = employee.get("employee_id")
        emp_name = employee.get("employee_name")
        dept = employee.get("department", "general").strip().lower()

        # 1. Select hardware based on department
        hardware = HARDWARE_CATALOG.get(dept, DEFAULT_HARDWARE)
        asset_tag = f"ASSET-{uuid.uuid4().hex[:8].upper()}"
        laptop_serial = f"SN-{uuid.uuid4().hex[:10].upper()}"

        # 2. Assign workspace
        floor = random.choice(WORKSPACE_FLOORS)
        zone = random.choice(DESK_ZONES)
        desk_id = f"DESK-{floor.replace(' ', '')}-{zone.replace(' ', '')}-{random.randint(1, 30):02d}"

        # 3. Issue access badge
        badge_id = f"BADGE-{uuid.uuid4().hex[:6].upper()}"
        badge_access_zones = ["MAIN LOBBY", "CAFETERIA", "EMERGENCY EXITS"]
        if dept in ["engineering", "operations", "forensics"]:
            badge_access_zones.append("SERVER ROOM")
        if dept == "forensics":
            badge_access_zones.append("SECURE EVIDENCE VAULT")

        return AgentResult(
            success=True,
            data={
                "resource_status": "ALLOCATED",
                "employee_id": emp_id,
                "employee_name": emp_name,
                "hardware_assignment": {
                    "asset_tag": asset_tag,
                    "laptop_model": hardware["laptop"],
                    "laptop_serial": laptop_serial,
                    "monitor": hardware["monitor"],
                    "peripherals": hardware["peripherals"],
                    "delivery_status": "READY_FOR_PICKUP"
                },
                "workspace": {
                    "desk_id": desk_id,
                    "location": f"{floor}, {zone}",
                    "phone_extension": f"EXT-{random.randint(1000, 9999)}"
                },
                "access_badge": {
                    "badge_id": badge_id,
                    "access_zones": badge_access_zones,
                    "expiry": "2027-12-31",
                    "status": "ACTIVE"
                },
                "allocated_at": datetime.utcnow().isoformat()
            },
            metadata={"agent": self.name, "handler": "allocate_resources"}
        )


# Singleton Resource Agent instance
resource_agent = ResourceAgent()
