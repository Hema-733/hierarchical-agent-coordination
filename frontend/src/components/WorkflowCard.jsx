// src/components/WorkflowCard.jsx — Summary card representing a single onboarding workflow
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
  } = workflow;

  const safeTasks = Array.isArray(tasks) ? tasks : [];

  // Calculate task completion statistics
  const totalTasks = safeTasks.length || 6;
  const completedTasks = safeTasks.filter((t) => t.status === "COMPLETED").length;
  const failedTasks = safeTasks.filter((t) => t.status === "FAILED").length;
  const progressPct = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  const formattedDate = created_at
    ? new Date(created_at).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Recently";

  return (
    <div className="workflow-card">
      <div className="workflow-card-header">
        <div>
          <div className="workflow-card-id">{workflow_id}</div>
          <div className="workflow-card-sub">Candidate: {employee_id}</div>
        </div>
        <TaskStatusBadge status={overall_status} />
      </div>

      {paused_reason && (
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
            className={`progress-fill ${failedTasks > 0 ? "has-failed" : ""}`}
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Card Footer */}
      <div className="workflow-card-footer">
        <span className="workflow-card-date">{formattedDate}</span>
        <Link to={`/workflows/${workflow_id}`} className="btn btn-secondary btn-sm">
          <span>Inspect DAG</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </Link>
      </div>
    </div>
  );
}
