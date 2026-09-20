// src/api/useWorkflowStream.js
// Custom hook — opens an SSE connection to the backend /workflow/{id}/stream endpoint.
// Streams real-time workflow events: task starts, completions, failures, retries, pauses, etc.

import { useState, useEffect, useRef, useCallback } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";

/**
 * useWorkflowStream(workflowId, enabled)
 *
 * @param {string}  workflowId  - Workflow to subscribe to
 * @param {boolean} enabled     - Set false to skip opening a connection (e.g., loading state)
 *
 * @returns {{
 *   events: Array<object>,       — Accumulated SSE events (newest last)
 *   connectionStatus: string,    — "connecting" | "connected" | "error" | "closed"
 *   clearEvents: function        — Empties the event list
 * }}
 */
export function useWorkflowStream(workflowId, enabled = true) {
  const [events, setEvents] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState("connecting");
  const esRef = useRef(null);

  const clearEvents = useCallback(() => setEvents([]), []);

  useEffect(() => {
    if (!workflowId || !enabled) return;

    // Clean up any previous connection
    if (esRef.current) {
      esRef.current.close();
    }

    const url = `${API_BASE}/workflow/${encodeURIComponent(workflowId)}/stream`;
    const es = new EventSource(url);
    esRef.current = es;
    setConnectionStatus("connecting");

    es.onopen = () => {
      setConnectionStatus("connected");
    };

    // Generic message handler — catches events that don't have a named type
    es.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data);
        if (evt.type === "ping") return; // keep-alive, discard
        setEvents((prev) => [...prev, evt]);
      } catch {
        // Ignore unparseable frames
      }
    };

    // Named event type handlers — FastAPI SSE sets event: <TYPE>
    const SSE_EVENT_TYPES = [
      "WORKFLOW_STARTED",
      "ROUND_STARTED",
      "TASK_READY",
      "AGENT_TASK_STARTED",
      "AGENT_TASK_COMPLETED",
      "TASK_FAILED",
      "TASK_RETRYING",
      "WORKFLOW_COMPLETED",
      "WORKFLOW_PAUSED",
      "WORKFLOW_RESUMED",
      "DOCUMENT_REVIEW_REQUIRED",
      "DOCUMENT_UPDATED",
      "DOCUMENT_VERIFIED",
      "DOCUMENT_REJECTED",
      "ping",
    ];

    SSE_EVENT_TYPES.forEach((eventType) => {
      es.addEventListener(eventType, (e) => {
        if (eventType === "ping") return;
        try {
          const evt = JSON.parse(e.data);
          setEvents((prev) => [...prev, evt]);
        } catch {
          // Ignore
        }
      });
    });

    es.onerror = () => {
      setConnectionStatus("error");
      // EventSource auto-reconnects — don't close here
    };

    return () => {
      es.close();
      esRef.current = null;
      setConnectionStatus("closed");
    };
  }, [workflowId, enabled]);

  return { events, connectionStatus, clearEvents };
}
