// src/components/WorkflowCard.jsx — Summary card representing a single onboarding workflow in the queue
import { Link } from "react-router-dom";
import TaskStatusBadge from "./TaskStatusBadge";

export default function WorkflowCard({ workflow }) {
  const {
    workflow_id,
    overall_status,
    employee_id,
    created_at,
    tasks,
    paused_reason,
    employee,
    metadata,
  } = workflow;

  const safeTasks = Array.isArray(tasks) ? tasks : [];

  // Calculate task completion statistics
  const totalTasks = safeTasks.length || 6;
  const completedTasks = safeTasks.filter((t) => t.status === "COMPLETED").length;
  const failedTasks = safeTasks.filter((t) => t.status === "FAILED").length;
  const progressPct = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  const candidateName = employee?.employee_name || employee_id;
  const candidateRole = employee?.designation ? `${employee.department} • ${employee.designation}` : null;

  const isActionRequired = overall_status === "ACTION_REQUIRED";
  const isPaused = overall_status === "PAUSED";
  const missingDocs = metadata?.missing_documents || [];

  const formattedDate = created_at
    ? new Date(created_at).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Recently";

  return (
    <div className={`workflow-card ${isActionRequired ? "workflow-card-action-required" : ""}`}>
      <div className="workflow-card-header">
        <div>
          <div className="workflow-candidate-name">{candidateName}</div>
          <div className="workflow-card-id">{workflow_id}</div>
          {candidateRole && <div className="workflow-card-sub">{candidateRole}</div>}
        </div>
        <TaskStatusBadge status={overall_status} />
      </div>

      {/* Action Required Notice */}
      {isActionRequired && (
        <div className="card-action-required-notice">
          <div className="action-notice-title">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <strong>Action Required: Missing Documents</strong>
          </div>
          <div className="action-notice-body">
            {missingDocs.length > 0 ? (
              <span>Missing: <strong>{missingDocs.join(", ")}</strong></span>
            ) : (
              <span>{paused_reason || "Missing mandatory verification documents."}</span>
            )}
          </div>
        </div>
      )}

      {/* Standard Paused Notice */}
      {isPaused && !isActionRequired && paused_reason && (
        <div className="card-paused-notice">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{paused_reason}</span>
        </div>
      )}

      {/* Progress Bar */}
      <div className="workflow-progress-section">
        <div className="progress-labels">
          <span>Task Progress</span>
          <span className="progress-count">
            {completedTasks}/{totalTasks} ({progressPct}%)
          </span>
        </div>
        <div className="progress-track">
          <div
            className={`progress-fill ${failedTasks > 0 ? "has-failed" : isActionRequired ? "is-action-required" : ""}`}
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Card Footer */}
      <div className="workflow-card-footer">
        <span className="workflow-card-date">{formattedDate}</span>
        <div style={{ display: "flex", gap: "6px" }}>
          {isActionRequired && (
            <Link
              to={`/workflows/${workflow_id}?tab=DOCUMENTS`}
              className="btn btn-warning btn-sm"
              style={{
                backgroundColor: "var(--status-warning-bg)",
                color: "var(--status-warning)",
                border: "1px solid var(--status-warning-border)",
                fontWeight: 600,
                fontSize: "0.75rem",
              }}
            >
              Review Docs
            </Link>
          )}
          <Link to={`/workflows/${workflow_id}`} className="btn btn-secondary btn-sm">
            <span>Inspect DAG</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </Link>
        </div>
      </div>
    </div>
  );
}

