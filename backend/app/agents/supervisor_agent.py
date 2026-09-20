"""
agents/supervisor_agent.py — Main Workflow Orchestrator.

Responsibilities:
- Maintains the registry of specialized sub-agents (HR, IT, Finance, Resource).
- Dispatches READY tasks to the appropriate sub-agent.
- Evaluates task results and updates the MongoDB state via repositories.
- Unlocks dependent tasks as their prerequisites complete.
- Manages overall workflow status (PENDING -> RUNNING -> COMPLETED / FAILED / PAUSED).
- Directly executes the 'Final Confirmation' consolidation task.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.agents.base_agent import BaseAgent, AgentResult
from app.models.task import TaskStatus
from app.models.workflow import WorkflowStatus
from app.db.repositories import task_repo, workflow_repo, employee_repo
from app.services.event_broker import event_broker


class SupervisorAgent(BaseAgent):
    """Central orchestrator in the hierarchical multi-agent architecture."""

    def __init__(self):
        super().__init__(
            agent_id="AGT-SUPERVISOR",
            name="Supervisor Agent",
            agent_type="SUPERVISOR",
            description="Main orchestrator responsible for workflow decomposition, task dispatching, dependency tracking, failure handling, and completion checks."
        )
        self._sub_agents: Dict[str, BaseAgent] = {}

    def register_sub_agent(self, agent: BaseAgent) -> None:
        """Registers a specialized sub-agent by its name and ID."""
        self._sub_agents[agent.name] = agent
        self._sub_agents[agent.agent_id] = agent
        print(f"[Supervisor] Registered sub-agent: {agent.name} ({agent.agent_id})")

    def get_agent_for_task(self, task: Dict[str, Any]) -> Optional[BaseAgent]:
        """Looks up the assigned agent in the registry."""
        agent_name = task.get("agent")
        if agent_name == self.name or agent_name == self.agent_id:
            return self
        return self._sub_agents.get(agent_name)

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Supervisor directly handles its own assigned tasks (e.g. 'Final Confirmation').
        """
        task_name = task.get("task_name")
        if task_name == "Final Confirmation":
            return await self._execute_final_confirmation(task, context)

        return AgentResult(
            success=True,
            data={"message": f"Supervisor handled task '{task_name}'"},
            metadata={"timestamp": datetime.utcnow().isoformat()}
        )

    async def _execute_final_confirmation(self, task: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Consolidates results from all completed sub-tasks into a final onboarding summary.
        """
        workflow_id = task.get("workflow_id")
        tasks = await task_repo.get_tasks_by_workflow(workflow_id)
        
        summary = {
            "onboarding_status": "SUCCESSFUL",
            "employee_id": context.get("employee", {}).get("employee_id"),
            "employee_name": context.get("employee", {}).get("employee_name"),
            "department": context.get("employee", {}).get("department"),
            "completed_milestones": [t["task_name"] for t in tasks if t["status"] == TaskStatus.COMPLETED.value],
            "verified_at": datetime.utcnow().isoformat(),
            "confirmation_code": f"CONF-ONBOARD-{workflow_id[-6:]}"
        }
        
        return AgentResult(
            success=True,
            data=summary,
            metadata={"orchestrator": self.name}
        )

    def evaluate_dependencies(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Determines which PENDING tasks have all prerequisites satisfied
        and are now ready to be unlocked into READY state.
        """
        completed_task_names = {
            t["task_name"] for t in tasks if t.get("status") == TaskStatus.COMPLETED.value
        }
        failed_task_names = {
            t["task_name"] for t in tasks if t.get("status") == TaskStatus.FAILED.value
        }

        tasks_to_unlock = []
        for t in tasks:
            if t.get("status") != TaskStatus.PENDING.value:
                continue

            dependencies = t.get("dependencies", [])
            # If any dependency failed, this task cannot run yet
            if any(dep in failed_task_names for dep in dependencies):
                continue

            # If all dependencies are COMPLETED, this task is ready
            if all(dep in completed_task_names for dep in dependencies):
                tasks_to_unlock.append(t)

        return tasks_to_unlock

    async def run_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Main orchestration loop.
        Executes tasks stage by stage until workflow finishes, pauses, or fails.
        """
        wf = await workflow_repo.get_workflow_by_id(workflow_id)
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        # Guard check: do not re-run completed workflows
        if wf["overall_status"] == WorkflowStatus.COMPLETED.value:
            return {"workflow_id": workflow_id, "status": wf["overall_status"], "message": "Workflow already completed."}

        # Transition workflow to RUNNING
        await workflow_repo.update_workflow_status(workflow_id, WorkflowStatus.RUNNING.value)

        # Load employee context
        employee_id = wf.get("employee_id")
        employee = await employee_repo.get_employee_by_id(employee_id) or {}
        context = {
            "workflow": wf,
            "employee": employee,
            "workflow_id": workflow_id
        }

        event_broker.publish(
            workflow_id=workflow_id,
            event_type="WORKFLOW_STARTED",
            message=f"Supervisor Agent initiated onboarding workflow for {employee.get('employee_name', employee_id)}.",
            status="RUNNING",
            data={"employee_id": employee_id, "department": employee.get("department")},
        )

        max_iterations = 20  # Safety circuit breaker
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            event_broker.publish(
                workflow_id=workflow_id,
                event_type="ROUND_STARTED",
                round_num=iteration,
                message=f"Supervisor evaluating dependency DAG round {iteration}...",
                status="RUNNING",
            )

            # --- PAUSE CHECKPOINT ---
            # Re-read workflow status from DB each iteration so that an external
            # POST /pause can cleanly halt execution without data loss.
            fresh_wf = await workflow_repo.get_workflow_by_id(workflow_id)
            if fresh_wf and fresh_wf.get("overall_status") == WorkflowStatus.PAUSED.value:
                print(f"[Supervisor] Workflow '{workflow_id}' is PAUSED. Halting execution loop.")
                paused_tasks = await task_repo.get_tasks_by_workflow(workflow_id)
                paused_completed = [t for t in paused_tasks if t.get("status") == TaskStatus.COMPLETED.value]
                return {
                    "workflow_id": workflow_id,
                    "status": WorkflowStatus.PAUSED.value,
                    "message": "Workflow paused externally. Resume to continue.",
                    "rounds": iteration - 1,
                    "completed_tasks": len(paused_completed),
                    "total_tasks": len(paused_tasks)
                }

            all_tasks = await task_repo.get_tasks_by_workflow(workflow_id)

            # Check if any tasks can be unlocked from PENDING to READY
            newly_ready = self.evaluate_dependencies(all_tasks)
            for t in newly_ready:
                await task_repo.update_task_status(t["task_id"], TaskStatus.READY.value)
                t["status"] = TaskStatus.READY.value
                event_broker.publish(
                    workflow_id=workflow_id,
                    event_type="TASK_READY",
                    task_id=t["task_id"],
                    task_name=t["task_name"],
                    agent=t.get("agent"),
                    round_num=iteration,
                    status="READY",
                    message=f"Prerequisites met. Task '{t['task_name']}' unlocked and READY for {t.get('agent')}.",
                )

            # Refresh list of ready tasks
            ready_tasks = [t for t in all_tasks if t.get("status") == TaskStatus.READY.value]

            # If no tasks are ready, assess overall status
            if not ready_tasks:
                pending = [t for t in all_tasks if t.get("status") == TaskStatus.PENDING.value]
                failed = [t for t in all_tasks if t.get("status") == TaskStatus.FAILED.value]
                completed = [t for t in all_tasks if t.get("status") == TaskStatus.COMPLETED.value]

                if len(completed) == len(all_tasks):
                    await workflow_repo.update_workflow_status(workflow_id, WorkflowStatus.COMPLETED.value)
                    event_broker.publish(
                        workflow_id=workflow_id,
                        event_type="WORKFLOW_COMPLETED",
                        round_num=iteration,
                        message="All onboarding tasks completed successfully across all specialized agents.",
                        status="COMPLETED",
                        data={"completed_tasks": len(completed), "total_tasks": len(all_tasks)},
                    )
                    return {
                        "workflow_id": workflow_id,
                        "status": WorkflowStatus.COMPLETED.value,
                        "message": "All onboarding tasks completed successfully.",
                        "rounds": iteration,
                        "completed_tasks": len(completed),
                        "total_tasks": len(all_tasks)
                    }
                elif failed:
                    # Only declare workflow FAILED if all failed tasks have exhausted retries
                    permanently_failed = [
                        t for t in failed
                        if t.get("retry_count", 0) >= t.get("max_retries", 3)
                    ]
                    if permanently_failed:
                        await workflow_repo.update_workflow_status(workflow_id, WorkflowStatus.FAILED.value)
                        failed_names = [t['task_name'] for t in permanently_failed]
                        return {
                            "workflow_id": workflow_id,
                            "status": WorkflowStatus.FAILED.value,
                            "message": f"Workflow halted permanently. Tasks exhausted retries: {failed_names}",
                            "rounds": iteration,
                            "completed_tasks": len(completed),
                            "total_tasks": len(all_tasks)
                        }
                    # Some failed tasks still have retries remaining — continue the loop
                    continue
                else:
                    # Tasks are waiting on external conditions or blocked
                    await workflow_repo.update_workflow_status(workflow_id, WorkflowStatus.PAUSED.value)
                    return {
                        "workflow_id": workflow_id,
                        "status": WorkflowStatus.PAUSED.value,
                        "message": "Workflow paused; awaiting required information.",
                        "rounds": iteration,
                        "completed_tasks": len(completed),
                        "total_tasks": len(all_tasks)
                    }

            # Execute all READY tasks in this round
            for task in ready_tasks:
                task_id = task["task_id"]
                task_name = task["task_name"]
                agent = self.get_agent_for_task(task)

                # Mark task as RUNNING
                await task_repo.update_task_status(task_id, TaskStatus.RUNNING.value, started=True)
                event_broker.publish(
                    workflow_id=workflow_id,
                    event_type="AGENT_TASK_STARTED",
                    task_id=task_id,
                    task_name=task_name,
                    agent=task.get("agent"),
                    round_num=iteration,
                    status="RUNNING",
                    message=f"{task.get('agent')} started execution on '{task_name}'.",
                )

                if not agent:
                    # If specialized agent is not registered yet (e.g. before Phases 6-9), simulate temporary success
                    result = AgentResult(
                        success=True,
                        data={"simulation": True, "task": task_name, "message": f"Simulated execution for {task['agent']}"},
                        metadata={"timestamp": datetime.utcnow().isoformat()}
                    )
                else:
                    try:
                        result = await agent.execute(task, context)
                    except Exception as e:
                        result = AgentResult(
                            success=False,
                            error=str(e),
                            metadata={"timestamp": datetime.utcnow().isoformat()}
                        )

                # Persist result and status
                if result.success:
                    await task_repo.update_task_status(
                        task_id=task_id,
                        status=TaskStatus.COMPLETED.value,
                        result=result.data,
                        completed=True
                    )
                    print(f"[Supervisor] Task '{task_name}' COMPLETED.")
                    event_broker.publish(
                        workflow_id=workflow_id,
                        event_type="AGENT_TASK_COMPLETED",
                        task_id=task_id,
                        task_name=task_name,
                        agent=task.get("agent"),
                        round_num=iteration,
                        status="COMPLETED",
                        message=f"{task.get('agent')} completed '{task_name}' successfully.",
                        data=result.data,
                    )
                else:
                    # Check if failure is human-resolvable (e.g. missing or unverified documents)
                    if result.data and result.data.get("needs_human_review"):
                        # DO NOT perform automatic retry loop. Do NOT burn retries.
                        await task_repo.update_task_status(
                            task_id=task_id,
                            status=TaskStatus.PAUSED.value,
                            error_message=result.error or "Waiting for human review",
                            result=result.data,
                            completed=False
                        )
                        pause_reason = result.data.get("reason", result.error or "Awaiting document verification")
                        missing_docs = result.data.get("missing_documents", [])

                        await workflow_repo.update_workflow_status(
                            workflow_id=workflow_id,
                            overall_status=WorkflowStatus.PAUSED.value,
                            metadata_patch={
                                "paused_reason": pause_reason,
                                "needs_human_review": True,
                                "missing_documents": missing_docs,
                                "blocked_task_id": task_id,
                                "blocked_task_name": task_name
                            }
                        )
                        # Also update top-level paused_reason and paused_at
                        collection = workflow_repo._get_collection()
                        await collection.update_one(
                            {"workflow_id": workflow_id},
                            {
                                "$set": {
                                    "paused_at": datetime.utcnow(),
                                    "paused_reason": pause_reason
                                }
                            }
                        )

                        print(f"[Supervisor] Task '{task_name}' requires human review ({pause_reason}). Halting loop and PAUSING workflow '{workflow_id}'.")

                        event_broker.publish(
                            workflow_id=workflow_id,
                            event_type="DOCUMENT_REVIEW_REQUIRED",
                            task_id=task_id,
                            task_name=task_name,
                            agent=task.get("agent"),
                            round_num=iteration,
                            status="PAUSED",
                            message=f"Human review required: {result.error}",
                            data=result.data,
                        )
                        event_broker.publish(
                            workflow_id=workflow_id,
                            event_type="WORKFLOW_PAUSED",
                            round_num=iteration,
                            status="PAUSED",
                            message=f"Workflow paused. Reason: {pause_reason}",
                            data={"paused_reason": pause_reason, "missing_documents": missing_docs, "blocked_task": task_name},
                        )

                        current_tasks = await task_repo.get_tasks_by_workflow(workflow_id)
                        current_completed = [t for t in current_tasks if t.get("status") == TaskStatus.COMPLETED.value]
                        return {
                            "workflow_id": workflow_id,
                            "status": WorkflowStatus.PAUSED.value,
                            "message": f"Workflow paused for human document review: {result.error}",
                            "rounds": iteration,
                            "needs_human_review": True,
                            "missing_documents": missing_docs,
                            "blocked_task_id": task_id,
                            "blocked_task_name": task_name,
                            "completed_tasks": len(current_completed),
                            "total_tasks": len(current_tasks)
                        }

                    # Re-fetch fresh task doc to get accurate retry_count for technical/transient failures
                    fresh_task = await task_repo.get_task_by_id(task_id)
                    retry_count = fresh_task.get("retry_count", 0)
                    max_retries = fresh_task.get("max_retries", 3)

                    if retry_count < max_retries:
                        # Auto-retry: increment counter and re-queue as READY
                        updated = await task_repo.increment_task_retry(task_id)
                        new_count = updated.get("retry_count", retry_count + 1)
                        print(
                            f"[Supervisor] Task '{task_name}' FAILED (attempt {retry_count + 1}/{max_retries + 1}). "
                            f"Auto-retrying (retry #{new_count})... Error: {result.error}"
                        )
                        event_broker.publish(
                            workflow_id=workflow_id,
                            event_type="TASK_RETRYING",
                            task_id=task_id,
                            task_name=task_name,
                            agent=task.get("agent"),
                            round_num=iteration,
                            status="READY",
                            message=f"Task '{task_name}' failed ({result.error}). Auto-retrying (attempt {new_count}/{max_retries + 1})...",
                            data={"retry_count": new_count, "error": result.error},
                        )
                    else:
                        # Permanently failed — exhausted all retries
                        await task_repo.update_task_status(
                            task_id=task_id,
                            status=TaskStatus.FAILED.value,
                            error_message=result.error or "Execution failed",
                            completed=True
                        )
                        print(
                            f"[Supervisor] Task '{task_name}' PERMANENTLY FAILED after {retry_count + 1} attempts."
                        )
                        event_broker.publish(
                            workflow_id=workflow_id,
                            event_type="TASK_FAILED",
                            task_id=task_id,
                            task_name=task_name,
                            agent=task.get("agent"),
                            round_num=iteration,
                            status="FAILED",
                            message=f"Task '{task_name}' permanently failed after {retry_count + 1} attempts. Error: {result.error}",
                            data={"error": result.error},
                        )

        final_tasks = await task_repo.get_tasks_by_workflow(workflow_id)
        final_completed = [t for t in final_tasks if t.get("status") == TaskStatus.COMPLETED.value]
        return {
            "workflow_id": workflow_id,
            "status": WorkflowStatus.RUNNING.value,
            "message": "Max iterations reached in current pass.",
            "rounds": max_iterations,
            "completed_tasks": len(final_completed),
            "total_tasks": len(final_tasks)
        }


# Singleton Supervisor instance across the application
supervisor_agent = SupervisorAgent()
