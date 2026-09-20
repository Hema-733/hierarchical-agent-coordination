"""
services/event_broker.py — Lightweight In-Memory Pub/Sub for Workflow SSE Streaming.

Manages per-workflow subscriber queues and maintains an event history buffer
so late-joining clients or reconnecting browsers receive recent activity.
Zero external broker dependencies (pure asyncio).
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Set, List, Optional, Any, Tuple


class WorkflowEventBroker:
    """In-memory event broker for streaming workflow events via Server-Sent Events."""

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        # Mapping: workflow_id -> Set of asyncio.Queue (one per connected SSE client)
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        # Mapping: workflow_id -> List of recent events
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._sequence = 0

    def subscribe(self, workflow_id: str) -> Tuple[asyncio.Queue, List[Dict[str, Any]]]:
        """
        Registers a new client queue for the given workflow.
        Returns the queue and a copy of any buffered past events.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        if workflow_id not in self._subscribers:
            self._subscribers[workflow_id] = set()
        self._subscribers[workflow_id].add(queue)

        history = list(self._history.get(workflow_id, []))
        return queue, history

    def unsubscribe(self, workflow_id: str, queue: asyncio.Queue) -> None:
        """Removes a client queue when an SSE connection drops or closes."""
        if workflow_id in self._subscribers:
            self._subscribers[workflow_id].discard(queue)
            if not self._subscribers[workflow_id]:
                del self._subscribers[workflow_id]

    def publish(
        self,
        workflow_id: str,
        event_type: str,
        message: str,
        agent: Optional[str] = None,
        task_id: Optional[str] = None,
        task_name: Optional[str] = None,
        status: Optional[str] = None,
        round_num: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Constructs and broadcasts an event to all subscribers of workflow_id,
        and saves it into the workflow's history buffer.
        """
        self._sequence += 1
        now_iso = datetime.utcnow().isoformat() + "Z"
        event = {
            "id": f"evt_{workflow_id}_{int(time.time()*1000)}_{self._sequence}",
            "workflow_id": workflow_id,
            "timestamp": now_iso,
            "type": event_type,
            "agent": agent or "Supervisor Agent",
            "task_id": task_id,
            "task_name": task_name,
            "status": status,
            "round": round_num,
            "message": message,
            "data": data or {},
        }

        # Save to history buffer
        if workflow_id not in self._history:
            self._history[workflow_id] = []
        self._history[workflow_id].append(event)
        if len(self._history[workflow_id]) > self.max_history:
            self._history[workflow_id].pop(0)

        # Broadcast to all active SSE subscriber queues for this workflow
        subscribers = self._subscribers.get(workflow_id, set())
        for q in list(subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Discard oldest or drop if buffer is saturated
                try:
                    q.get_nowait()
                    q.put_nowait(event)
                except Exception:
                    pass

        return event

    def get_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Returns the in-memory event buffer for a workflow."""
        return list(self._history.get(workflow_id, []))


# Global singleton instance across FastAPI app
event_broker = WorkflowEventBroker()
