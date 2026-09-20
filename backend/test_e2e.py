"""
test_e2e.py — End-to-End Integration Test Suite for Hierarchical Agent Coordination.

Validates the full multi-agent lifecycle:
1. Application startup and MongoDB connection (with automatic in-memory fallback)
2. Agent seeding and registration with the Supervisor
3. Health check verification
4. Employee onboarding initiation (POST /onboarding/)
5. Workflow state inspection and task graph verification (GET /workflow/{id})
6. Supervisor autonomous coordination & DAG execution (POST /workflow/{id}/execute)
7. Rich workflow summary aggregation (GET /workflow/{id}/summary)
8. AI narrative generation with graceful fallback (GET /workflow/{id}/ai-summary)
9. Workflow pause and resume controls (POST /workflow/{id}/pause, POST /workflow/{id}/resume)
10. Task retry mechanics (POST /task/{id}/retry)
"""

import sys
import asyncio
import time
import httpx
from datetime import date

# Ensure Windows terminal handles UTF-8 smoothly
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.main import app, lifespan

PASS = "[PASS]"
FAIL = "[FAIL]"


async def run_integration_tests():
    print("=" * 70)
    print("  HIERARCHICAL AGENT COORDINATION — END-TO-END INTEGRATION TEST SUITE")
    print("=" * 70)

    # Initialize application lifespan context
    async with lifespan(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
            
            # -----------------------------------------------------------------
            # TEST 1: Health Check Endpoint
            # -----------------------------------------------------------------
            print("\n[Test 1] Health Check (GET /health)...")
            res = await client.get("/health")
            assert res.status_code == 200, f"Health check failed with code {res.status_code}"
            data = res.json()
            assert data["status"] == "ok"
            print(f"  {PASS} App is running healthy: {data['app']} v{data['version']}")

            # -----------------------------------------------------------------
            # TEST 2: Verify Seeded Agents
            # -----------------------------------------------------------------
            print("\n[Test 2] Seeded Agents Inspection (GET /agent/)...")
            res = await client.get("/agent/")
            assert res.status_code == 200, f"Agents fetch failed with {res.status_code}"
            agents = res.json()
            assert len(agents) >= 5, f"Expected at least 5 seeded agents, found {len(agents)}"
            agent_names = [a["agent_name"] for a in agents]
            print(f"  {PASS} Seeded agents confirmed ({len(agents)} active):")
            for a in agents:
                print(f"     - [{a['agent_type']}] {a['agent_name']} ({a['status']})")

            # -----------------------------------------------------------------
            # TEST 3: Submit Employee Onboarding Request
            # -----------------------------------------------------------------
            print("\n[Test 3] Initiate Employee Onboarding (POST /onboarding/)...")
            test_ts = int(time.time())
            employee_payload = {
                "employee_name": "Alex Rivera",
                "email": f"alex.rivera.{test_ts}@techcorp.io",
                "phone": "+1-555-019-2834",
                "department": "Engineering",
                "designation": "Senior Frontend Engineer",
                "joining_date": str(date.today()),
                "manager": "Elena Rostova (Director)",
                "documents": {
                    "id_proof_submitted": True,
                    "address_proof_submitted": True,
                    "bank_details_submitted": True,
                    "education_certs_submitted": True,
                },
            }
            res = await client.post("/onboarding/", json=employee_payload)
            assert res.status_code == 201, f"Onboarding failed: {res.text}"
            onboarding_res = res.json()
            emp = onboarding_res["employee"]
            wf = onboarding_res["workflow"]
            wf_id = wf["workflow_id"]
            emp_id = emp["employee_id"]
            print(f"  {PASS} Employee successfully registered:")
            print(f"     - Employee ID: {emp_id} ({emp['employee_name']})")
            print(f"     - Workflow ID: {wf_id} (Status: {wf['overall_status']})")

            # -----------------------------------------------------------------
            # TEST 4: Query Workflow Details & Tasks
            # -----------------------------------------------------------------
            print(f"\n[Test 4] Verify Instantiated Workflow DAG (GET /workflow/{wf_id})...")
            res = await client.get(f"/workflow/{wf_id}")
            assert res.status_code == 200, f"Workflow query failed: {res.text}"
            wf_data = res.json()
            tasks = wf_data.get("tasks", [])
            assert len(tasks) == 6, f"Expected 6 tasks in onboarding pipeline, got {len(tasks)}"
            print(f"  {PASS} 6 dependency-aware tasks instantiated in PENDING state:")
            for t in tasks:
                deps = f" (prereqs: {t['dependencies']})" if t['dependencies'] else " (no prereqs)"
                print(f"     - [{t['status']}] {t['task_name']} -> {t['agent']}{deps}")

            # -----------------------------------------------------------------
            # TEST 5: Trigger Supervisor Coordination Loop
            # -----------------------------------------------------------------
            print(f"\n[Test 5] Execute Supervisor Coordination Loop (POST /workflow/{wf_id}/execute)...")
            res = await client.post(f"/workflow/{wf_id}/execute")
            assert res.status_code == 200, f"Workflow execution failed: {res.text}"
            exec_summary = res.json()["execution_summary"]
            print(f"  {PASS} Supervisor completed orchestration:")
            print(f"     - Status: {exec_summary.get('status')}")
            print(f"     - Rounds executed: {exec_summary.get('rounds')}")
            print(f"     - Completed tasks: {exec_summary.get('completed_tasks')}/{exec_summary.get('total_tasks')}")

            # Verify all tasks completed
            res = await client.get(f"/workflow/{wf_id}")
            wf_after = res.json()
            assert wf_after["overall_status"] == "COMPLETED", f"Expected COMPLETED, got {wf_after['overall_status']}"
            all_completed = all(t["status"] == "COMPLETED" for t in wf_after["tasks"])
            assert all_completed, "Not all tasks reached COMPLETED status"
            print(f"  {PASS} All 6 tasks successfully transitioned to COMPLETED:")
            for t in wf_after["tasks"]:
                print(f"     - {PASS} {t['task_name']} ({t['agent']}) - Done")

            # -----------------------------------------------------------------
            # TEST 6: Structured Workflow Summary
            # -----------------------------------------------------------------
            print(f"\n[Test 6] Fetch Aggregated Summary (GET /workflow/{wf_id}/summary)...")
            res = await client.get(f"/workflow/{wf_id}/summary")
            assert res.status_code == 200, f"Summary failed: {res.text}"
            summary_data = res.json()
            progress = summary_data["progress"]
            assert progress["progress_pct"] == 100.0, f"Expected 100% progress, got {progress['progress_pct']}"
            print(f"  {PASS} Progress: {progress['progress_pct']}% ({progress['completed']}/{progress['total_tasks']} tasks)")
            print("     Agent contributions:")
            for agent, stats in summary_data["agent_contributions"].items():
                print(f"       - {agent}: {stats.get('tasks_completed', stats.get('completed', 0))} completed, {stats.get('tasks_failed', stats.get('failed', 0))} failed")

            # -----------------------------------------------------------------
            # TEST 7: AI Status Narrative
            # -----------------------------------------------------------------
            print(f"\n[Test 7] Generate AI Narrative (GET /workflow/{wf_id}/ai-summary)...")
            res = await client.get(f"/workflow/{wf_id}/ai-summary")
            assert res.status_code == 200, f"AI summary failed: {res.text}"
            ai_data = res.json()
            ai_text = ai_data.get("ai_summary") or ai_data.get("summary")
            assert ai_text and len(ai_text) > 20, f"Expected non-empty AI narrative, got: {ai_data}"
            print(f"  {PASS} Narrative generated (model: {ai_data.get('model', 'fallback')}):")
            print(f"     \"{ai_text}\"")

            # -----------------------------------------------------------------
            # TEST 8: Pause and Resume Controls
            # -----------------------------------------------------------------
            print("\n[Test 8] Test Pause & Resume Controls on a second candidate...")
            second_emp = {
                "employee_name": "Jordan Lee",
                "email": f"jordan.lee.{test_ts}@techcorp.io",
                "phone": "+1-555-098-7654",
                "department": "Finance",
                "designation": "Financial Analyst",
                "joining_date": str(date.today()),
                "manager": "Marcus Vance",
                "documents": {
                    "id_proof_submitted": True,
                    "address_proof_submitted": True,
                    "bank_details_submitted": False,
                    "education_certs_submitted": True,
                },
            }
            res2 = await client.post("/onboarding/", json=second_emp)
            wf2_id = res2.json()["workflow"]["workflow_id"]

            # Pause workflow
            res_pause = await client.post(f"/workflow/{wf2_id}/pause", json={"reason": "Awaiting bank documentation"})
            assert res_pause.status_code == 200
            assert res_pause.json()["overall_status"] == "PAUSED"
            print(f"  {PASS} Workflow {wf2_id} successfully paused.")

            # Resume workflow
            res_resume = await client.post(f"/workflow/{wf2_id}/resume")
            assert res_resume.status_code == 200
            wf2_resumed = res_resume.json()
            print(f"  {PASS} Workflow {wf2_id} resumed. Status: {wf2_resumed['overall_status']}")

            # -----------------------------------------------------------------
            # TEST 9: Task Retry Mechanics
            # -----------------------------------------------------------------
            print("\n[Test 9] Test Task Retry Endpoint (POST /task/{id}/retry)...")
            from app.db.repositories import task_repo
            from app.models.task import TaskStatus

            # 9a: Verify non-FAILED task cannot be retried
            sample_task_id = tasks[0]["task_id"]
            res_retry_invalid = await client.post(f"/task/{sample_task_id}/retry")
            assert res_retry_invalid.status_code == 400, "Should reject retry of non-FAILED task"
            print(f"  {PASS} Validation confirmed: correctly rejected retry for COMPLETED task.")

            # 9b: Simulate a FAILED task with retry budget remaining
            await task_repo.update_task_status(sample_task_id, TaskStatus.FAILED.value, error_message="Simulated network failure")
            # Ensure retry_count is 0
            await task_repo._get_collection().update_one({"task_id": sample_task_id}, {"$set": {"retry_count": 0}})

            res_retry = await client.post(f"/task/{sample_task_id}/retry")
            assert res_retry.status_code == 200, f"Retry failed: {res_retry.text}"
            retried_task = res_retry.json()
            assert retried_task["status"] == "READY"
            assert retried_task["retry_count"] == 1
            print(f"  {PASS} Task {sample_task_id} successfully re-queued as READY (retry_count: {retried_task['retry_count']})")

            # -----------------------------------------------------------------
            # TEST 10: List Workflows & Employees
            # -----------------------------------------------------------------
            print("\n[Test 10] List Workflows and Employees API...")
            res_wfs = await client.get("/workflow/")
            assert res_wfs.status_code == 200
            wfs = res_wfs.json()
            assert len(wfs) >= 2
            print(f"  {PASS} GET /workflow/ returned {len(wfs)} workflows.")

            res_emps = await client.get("/onboarding/employees")
            assert res_emps.status_code == 200
            emps = res_emps.json()
            assert len(emps) >= 2
            print(f"  {PASS} GET /onboarding/employees returned {len(emps)} employees.")

    print("\n" + "=" * 70)
    print("  ALL 10 END-TO-END INTEGRATION TESTS PASSED SUCCESSFULLY!  ")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(run_integration_tests())
    except Exception as e:
        print(f"\n{FAIL} INTEGRATION TEST FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
