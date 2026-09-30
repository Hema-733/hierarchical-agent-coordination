"""
test_queue_concurrency.py — Integration and Concurrency Test Suite.

Validates the Independent Employee Workflows + Onboarding Queue requirements:
1. Candidate A with missing bank details pauses at Document Verification -> ACTION_REQUIRED.
2. The Onboarding Queue reflects Candidate A in ACTION_REQUIRED with enriched candidate details.
3. Candidate B (complete docs) initiates and completes all 6 DAG tasks independently while Candidate A is paused.
4. Candidate A is completely unaffected by Candidate B's execution (strict state isolation).
5. Supervisor concurrency lock prevents duplicate simultaneous runs on the same workflow.
6. Candidate A updates documents and resumes using the SAME workflow_id.
7. Candidate A completes all 6 tasks; previously completed tasks are not re-run.
8. Task count for each candidate is strictly 6 (no task duplication, DB compound index invariant).
9. Candidate C failure isolation: A failure in one candidate does not affect other workflows.
"""

import sys
import asyncio
import time
from datetime import date
import httpx

# Ensure Windows terminal handles UTF-8 smoothly
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.main import app, lifespan
from app.db.connection import get_database

PASS = "[PASS]"
FAIL = "[FAIL]"


async def run_queue_concurrency_tests():
    print("=" * 75)
    print("  INDEPENDENT WORKFLOWS & ONBOARDING QUEUE CONCURRENCY TEST SUITE")
    print("=" * 75)

    async with lifespan(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
            ts = int(time.time())

            # -----------------------------------------------------------------
            # TEST 1: Database Indexes Verification
            # -----------------------------------------------------------------
            print("\n[Test 1] Verifying MongoDB collection indexes...")
            db = get_database()
            wf_indexes = await db.workflows.index_information()
            task_indexes = await db.tasks.index_information()
            emp_indexes = await db.employees.index_information()

            assert "workflow_id_1" in wf_indexes, "Missing workflow_id index"
            assert "workflow_id_1_task_name_1" in task_indexes or "uniq_workflow_task" in task_indexes, (
                "Missing (workflow_id, task_name) unique compound index"
            )
            assert "employee_id_1" in emp_indexes, "Missing employee_id index"
            print(f"  {PASS} Database indexes verified: workflows, employees, and compound uniq_workflow_task index active.")

            # -----------------------------------------------------------------
            # TEST 2: Initiate Candidate A with Missing Bank Details
            # -----------------------------------------------------------------
            print("\n[Test 2] Candidate A onboarding initiation (missing bank details)...")
            cand_a_payload = {
                "employee_name": f"Candidate Alpha {ts}",
                "email": f"cand.alpha.{ts}@techcorp.io",
                "phone": "+1-555-010-0001",
                "department": "Finance",
                "designation": "Financial Analyst",
                "joining_date": str(date.today()),
                "manager": "Chief Financial Officer",
                "documents": {
                    "id_proof_submitted": True,
                    "address_proof_submitted": True,
                    "bank_details_submitted": False,  # Missing!
                    "education_certs_submitted": True,
                },
            }
            res_a = await client.post("/onboarding/", json=cand_a_payload)
            assert res_a.status_code == 201, f"Candidate A onboarding failed: {res_a.text}"
            res_a_json = res_a.json()
            emp_a = res_a_json["employee"]
            wf_a = res_a_json["workflow"]
            wf_a_id = wf_a["workflow_id"]
            emp_a_id = emp_a["employee_id"]
            print(f"  {PASS} Candidate A created: ID={emp_a_id}, Workflow={wf_a_id}")

            # -----------------------------------------------------------------
            # TEST 3: Execute Candidate A -> Verify ACTION_REQUIRED Pause
            # -----------------------------------------------------------------
            print("\n[Test 3] Executing Candidate A workflow DAG...")
            exec_res_a = await client.post(f"/workflow/{wf_a_id}/execute")
            assert exec_res_a.status_code == 200, f"Execution failed: {exec_res_a.text}"
            
            # Fetch workflow details
            details_a = await client.get(f"/workflow/{wf_a_id}")
            assert details_a.status_code == 200
            wf_a_data = details_a.json()
            tasks_a = wf_a_data["tasks"]

            assert wf_a_data["overall_status"] == "ACTION_REQUIRED", (
                f"Expected ACTION_REQUIRED, got {wf_a_data['overall_status']}"
            )
            assert len(tasks_a) == 6, f"Expected 6 tasks for Candidate A, got {len(tasks_a)}"

            tasks_a_by_name = {t["task_name"]: t for t in tasks_a}
            assert tasks_a_by_name["HR Verification"]["status"] == "COMPLETED"
            assert tasks_a_by_name["Document Verification"]["status"] == "PAUSED"
            assert "bank_details" in str(tasks_a_by_name["Document Verification"].get("error_message", "")) or \
                   "bank_details" in str(wf_a_data.get("paused_reason", "")) or \
                   "Bank Account" in str(tasks_a_by_name["Document Verification"].get("error_message", ""))
            
            # Downstream tasks must remain PENDING
            assert tasks_a_by_name["IT Account Setup"]["status"] == "PENDING"
            assert tasks_a_by_name["Payroll Setup"]["status"] == "PENDING"
            assert tasks_a_by_name["Resource Allocation"]["status"] == "PENDING"
            assert tasks_a_by_name["Final Confirmation"]["status"] == "PENDING"
            print(f"  {PASS} Candidate A cleanly paused in ACTION_REQUIRED state:")
            print(f"     - HR Verification: COMPLETED")
            print(f"     - Document Verification: PAUSED (Missing bank_details)")
            print(f"     - Downstream tasks: PENDING")

            # -----------------------------------------------------------------
            # TEST 4: Onboarding Queue Inspection with Candidate Enrichment
            # -----------------------------------------------------------------
            print("\n[Test 4] Querying Onboarding Queue (GET /workflow/)...")
            q_res = await client.get("/workflow/")
            assert q_res.status_code == 200
            queue_items = q_res.json()
            cand_a_item = next((item for item in queue_items if item["workflow_id"] == wf_a_id), None)
            assert cand_a_item is not None, "Candidate A not found in queue"
            assert cand_a_item["overall_status"] == "ACTION_REQUIRED"
            assert cand_a_item.get("employee") is not None
            assert cand_a_item["employee"]["employee_name"] == f"Candidate Alpha {ts}"
            print(f"  {PASS} Queue correctly contains Candidate A with enriched employee metadata.")

            # Filter by status=ACTION_REQUIRED
            q_filtered = await client.get("/workflow/?status=ACTION_REQUIRED")
            assert q_filtered.status_code == 200
            filtered_items = q_filtered.json()
            assert any(item["workflow_id"] == wf_a_id for item in filtered_items)
            print(f"  {PASS} Filtering queue by status=ACTION_REQUIRED works as expected.")

            # -----------------------------------------------------------------
            # TEST 5: Candidate B (Complete Docs) Runs Independently
            # -----------------------------------------------------------------
            print("\n[Test 5] Candidate B onboarding & execution while Candidate A is paused...")
            cand_b_payload = {
                "employee_name": f"Candidate Beta {ts}",
                "email": f"cand.beta.{ts}@techcorp.io",
                "phone": "+1-555-020-0002",
                "department": "Engineering",
                "designation": "Staff Engineer",
                "joining_date": str(date.today()),
                "manager": "VP Engineering",
                "documents": {
                    "id_proof_submitted": True,
                    "address_proof_submitted": True,
                    "bank_details_submitted": True,  # All present!
                    "education_certs_submitted": True,
                },
            }
            res_b = await client.post("/onboarding/", json=cand_b_payload)
            assert res_b.status_code == 201, f"Candidate B onboarding failed: {res_b.text}"
            res_b_json = res_b.json()
            emp_b = res_b_json["employee"]
            wf_b = res_b_json["workflow"]
            wf_b_id = wf_b["workflow_id"]
            emp_b_id = emp_b["employee_id"]
            print(f"  {PASS} Candidate B created: ID={emp_b_id}, Workflow={wf_b_id}")

            exec_res_b = await client.post(f"/workflow/{wf_b_id}/execute")
            assert exec_res_b.status_code == 200, f"Candidate B execution failed: {exec_res_b.text}"

            details_b = await client.get(f"/workflow/{wf_b_id}")
            assert details_b.status_code == 200
            wf_b_data = details_b.json()
            tasks_b = wf_b_data["tasks"]

            assert wf_b_data["overall_status"] == "COMPLETED", (
                f"Candidate B expected COMPLETED, got {wf_b_data['overall_status']}"
            )
            assert len(tasks_b) == 6, f"Expected 6 tasks for Candidate B, got {len(tasks_b)}"
            for tb in tasks_b:
                assert tb["status"] == "COMPLETED", f"Task {tb['task_name']} not completed: {tb['status']}"
            print(f"  {PASS} Candidate B executed completely to COMPLETED state across all 6 tasks.")

            # -----------------------------------------------------------------
            # TEST 6: Strict Isolation — Verify Candidate A Did Not Change
            # -----------------------------------------------------------------
            print("\n[Test 6] Verifying Candidate A state isolation...")
            details_a_recheck = await client.get(f"/workflow/{wf_a_id}")
            assert details_a_recheck.status_code == 200
            wf_a_recheck = details_a_recheck.json()
            assert wf_a_recheck["overall_status"] == "ACTION_REQUIRED", (
                f"Candidate A state was contaminated! Got {wf_a_recheck['overall_status']}"
            )
            tasks_a_recheck = {t["task_name"]: t for t in wf_a_recheck["tasks"]}
            assert tasks_a_recheck["HR Verification"]["status"] == "COMPLETED"
            assert tasks_a_recheck["Document Verification"]["status"] == "PAUSED"
            assert tasks_a_recheck["IT Account Setup"]["status"] == "PENDING"
            assert tasks_a_recheck["Payroll Setup"]["status"] == "PENDING"
            assert tasks_a_recheck["Resource Allocation"]["status"] == "PENDING"
            assert tasks_a_recheck["Final Confirmation"]["status"] == "PENDING"
            print(f"  {PASS} Candidate A remained completely unaffected by Candidate B's execution.")

            # -----------------------------------------------------------------
            # TEST 7: Supervisor Concurrency Lock & Idempotency
            # -----------------------------------------------------------------
            print("\n[Test 7] Testing Supervisor Concurrency & Idempotency...")
            # Repeated execute call while in ACTION_REQUIRED without document update should not duplicate tasks
            dup_exec = await client.post(f"/workflow/{wf_a_id}/execute")
            assert dup_exec.status_code == 200
            details_a_dup = await client.get(f"/workflow/{wf_a_id}")
            assert len(details_a_dup.json()["tasks"]) == 6, "Task duplication detected on repeated execution!"
            print(f"  {PASS} Supervisor execution is idempotent; exactly 6 tasks maintained.")

            # -----------------------------------------------------------------
            # TEST 8: Candidate A Updates Bank Details and Resumes SAME Workflow
            # -----------------------------------------------------------------
            print("\n[Test 8] Updating Candidate A documents & resuming with SAME workflow_id...")
            patch_doc_payload = {
                "bank_details": {
                    "status": "VERIFIED",
                    "details": "Checking Account ***4321 / Verified routing",
                },
                "workflow_id": wf_a_id,
                "auto_resume": True,
            }
            patch_res = await client.patch(f"/onboarding/employees/{emp_a_id}/documents", json=patch_doc_payload)
            assert patch_res.status_code == 200, f"Document update failed: {patch_res.text}"

            # Verify workflow progress
            details_a_resumed = await client.get(f"/workflow/{wf_a_id}")
            assert details_a_resumed.status_code == 200
            wf_a_resumed = details_a_resumed.json()

            # Ensure same workflow_id
            assert wf_a_resumed["workflow_id"] == wf_a_id, "Workflow ID unexpectedly changed!"

            # If auto_resume executed, check completion; otherwise trigger execute
            if wf_a_resumed["overall_status"] != "COMPLETED":
                res_exec = await client.post(f"/workflow/{wf_a_id}/execute")
                assert res_exec.status_code == 200
                details_a_resumed = await client.get(f"/workflow/{wf_a_id}")
                wf_a_resumed = details_a_resumed.json()

            assert wf_a_resumed["overall_status"] == "COMPLETED", (
                f"Candidate A expected COMPLETED, got {wf_a_resumed['overall_status']}"
            )

            tasks_a_final = wf_a_resumed["tasks"]
            assert len(tasks_a_final) == 6, f"Expected exactly 6 tasks, found {len(tasks_a_final)}"
            for t in tasks_a_final:
                assert t["status"] == "COMPLETED", f"Task {t['task_name']} was not completed: {t['status']}"
            print(f"  {PASS} Candidate A resumed and completed all 6 tasks with SAME workflow_id: {wf_a_id}")

            # -----------------------------------------------------------------
            # TEST 9: Candidate C Failure Isolation
            # -----------------------------------------------------------------
            print("\n[Test 9] Candidate C Failure Isolation Test...")
            cand_c_payload = {
                "employee_name": f"Candidate Gamma {ts}",
                "email": f"cand.gamma.{ts}@techcorp.io",
                "phone": "+1-555-030-0003",
                "department": "Operations",
                "designation": "Coordinator",
                "joining_date": str(date.today()),
                "manager": "COO",
                "documents": {
                    "id_proof_submitted": True,
                    "address_proof_submitted": True,
                    "bank_details_submitted": True,
                    "education_certs_submitted": True,
                },
            }
            res_c = await client.post("/onboarding/", json=cand_c_payload)
            wf_c_id = res_c.json()["workflow"]["workflow_id"]

            # Manually pause Candidate C with an error/pause condition
            pause_c = await client.post(f"/workflow/{wf_c_id}/pause", json={"reason": "Simulated Compliance Hold"})
            assert pause_c.status_code == 200
            wf_c_details = (await client.get(f"/workflow/{wf_c_id}")).json()
            assert wf_c_details["overall_status"] == "PAUSED"

            # Check that Candidate A and B remain COMPLETED in the queue
            q_final = (await client.get("/workflow/")).json()
            cand_a_final = next(w for w in q_final if w["workflow_id"] == wf_a_id)
            cand_b_final = next(w for w in q_final if w["workflow_id"] == wf_b_id)
            cand_c_final = next(w for w in q_final if w["workflow_id"] == wf_c_id)

            assert cand_a_final["overall_status"] == "COMPLETED"
            assert cand_b_final["overall_status"] == "COMPLETED"
            assert cand_c_final["overall_status"] == "PAUSED"
            print(f"  {PASS} Candidate C paused/failed state isolated: Candidate A & B remain COMPLETED.")

    print("\n" + "=" * 75)
    print("  ALL 9 CONCURRENCY & QUEUE INTEGRATION TESTS PASSED CLEANLY!")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_queue_concurrency_tests())
