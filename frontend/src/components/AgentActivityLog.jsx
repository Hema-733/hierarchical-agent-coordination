// src/components/AgentActivityLog.jsx — Real-time event log and agent action inspector
import { useState } from "react";
import TaskStatusBadge from "./TaskStatusBadge";

export default function AgentActivityLog({ tasks = [] }) {
  const [expandedTaskId, setExpandedTaskId] = useState(null);

  // Filter tasks that have at least started or completed
  const activeEvents = tasks.filter(
    (t) => t.status === "COMPLETED" || t.status === "RUNNING" || t.status === "FAILED" || t.retry_count > 0
  );

  const toggleExpand = (id) => {
    setExpandedTaskId((prev) => (prev === id ? null : id));
  };

  const getAgentColor = (agentName = "") => {
    if (agentName.includes("Supervisor")) return "#6366f1";
    if (agentName.includes("HR")) return "#ec4899";
    if (agentName.includes("IT")) return "#06b6d4";
    if (agentName.includes("Finance")) return "#10b981";
    if (agentName.includes("Resource")) return "#f59e0b";
    return "#8b5cf6";
  };

  if (activeEvents.length === 0) {
    return (
      <div className="glass-panel activity-log-empty">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        <p>No agent activity recorded yet. Trigger workflow execution to begin coordination.</p>
      </div>
    );
  }

  return (
    <div className="activity-log-container">
      <div className="activity-timeline">
        {activeEvents.map((task) => {
          const isExpanded = expandedTaskId === task.task_id;
          const agentColor = getAgentColor(task.agent);

          return (
            <div key={task.task_id} className="timeline-entry">
              {/* Timeline marker */}
              <div className="timeline-marker" style={{ borderColor: agentColor, backgroundColor: `${agentColor}20` }}>
                <span style={{ color: agentColor, fontSize: "0.75rem", fontWeight: 700 }}>
                  {task.agent ? task.agent.split(" ")[0][0] : "A"}
                </span>
              </div>

              {/* Event Content */}
              <div className="timeline-body glass-panel">
                <div className="timeline-header" onClick={() => toggleExpand(task.task_id)}>
                  <div className="timeline-title-row">
                    <span className="agent-tag" style={{ color: agentColor, backgroundColor: `${agentColor}15` }}>
                      {task.agent}
                    </span>
                    <span className="task-title-text">{task.task_name}</span>
                  </div>

                  <div className="timeline-meta-row">
                    {task.retry_count > 0 && (
                      <span className="badge badge-warning" style={{ fontSize: "0.7rem", padding: "2px 6px" }}>
                        Retry #{task.retry_count}
                      </span>
                    )}
                    <TaskStatusBadge status={task.status} size="sm" />
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      style={{ padding: "3px 8px", fontSize: "0.75rem" }}
                    >
                      {isExpanded ? "Collapse" : "Inspect"}
                    </button>
                  </div>
                </div>

                {/* Expanded Payload & Diagnostics */}
                {isExpanded && (
                  <div className="timeline-expanded-content">
                    {task.error_message && (
                      <div className="timeline-error-box">
                        <strong>Error: </strong> {task.error_message}
                      </div>
                    )}

                    {task.result && (
                      <div className="timeline-result-box">
                        <div className="payload-label">Execution Output Data:</div>
                        <pre className="json-pre">{JSON.stringify(task.result, null, 2)}</pre>
                      </div>
                    )}

                    <div className="timeline-timestamps">
                      {task.started_at && <span>Started: {new Date(task.started_at).toLocaleTimeString()}</span>}
                      {task.completed_at && <span>Completed: {new Date(task.completed_at).toLocaleTimeString()}</span>}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
