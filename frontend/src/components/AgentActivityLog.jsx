// src/components/AgentActivityLog.jsx
// Real-time SSE-based activity log — consumes live workflow events streamed from the backend.
import TaskStatusBadge from "./TaskStatusBadge";

// ── Event-type metadata ──────────────────────────────────────────────────────
const EVENT_META = {
  WORKFLOW_STARTED:     { icon: "▶", label: "Workflow Started",     color: "var(--accent)" },
  ROUND_STARTED:        { icon: "⟳", label: "Round Evaluated",      color: "var(--text-muted)" },
  TASK_READY:           { icon: "◆", label: "Task Unlocked",        color: "#4f88f5" },
  AGENT_TASK_STARTED:   { icon: "◉", label: "Agent Started",        color: "#f59e0b" },
  AGENT_TASK_COMPLETED: { icon: "✓", label: "Task Completed",       color: "#22c55e" },
  TASK_FAILED:          { icon: "✕", label: "Task Failed",          color: "#ef4444" },
  TASK_RETRYING:        { icon: "↺", label: "Retrying",             color: "#f59e0b" },
  WORKFLOW_PAUSED:      { icon: "⏸", label: "Workflow Paused",      color: "#94a3b8" },
  WORKFLOW_RESUMED:     { icon: "▶", label: "Workflow Resumed",     color: "var(--accent)" },
  DOCUMENT_REVIEW_REQUIRED: { icon: "⚠", label: "Action Required", color: "var(--status-warning)" },
  DOCUMENT_UPDATED:         { icon: "✎", label: "Doc Updated",      color: "var(--accent)" },
  DOCUMENT_VERIFIED:        { icon: "✓", label: "Doc Verified",     color: "var(--status-success)" },
  DOCUMENT_REJECTED:        { icon: "✕", label: "Doc Rejected",     color: "var(--status-danger)" },
};

function formatTime(isoStr) {
  if (!isoStr) return "";
  try {
    return new Date(isoStr).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return isoStr;
  }
}

// ── Connection status pill ───────────────────────────────────────────────────
function ConnectionPill({ status }) {
  const config = {
    connecting: { label: "Connecting...", color: "#f59e0b" },
    connected:  { label: "Live",          color: "#22c55e" },
    error:      { label: "Reconnecting",  color: "#ef4444" },
    closed:     { label: "Disconnected",  color: "#94a3b8" },
  }[status] || { label: status, color: "#94a3b8" };

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "5px",
        fontSize: "0.72rem",
        fontWeight: 600,
        color: config.color,
        letterSpacing: "0.02em",
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          backgroundColor: config.color,
          display: "inline-block",
          boxShadow: status === "connected" ? `0 0 6px ${config.color}` : "none",
          animation: status === "connected" ? "pulse 2s ease-in-out infinite" : "none",
        }}
      />
      {config.label}
    </span>
  );
}

// ── Single event row ─────────────────────────────────────────────────────────
function EventRow({ event, index }) {
  const meta = EVENT_META[event.type] || { icon: "•", label: event.type, color: "var(--text-muted)" };

  // Round label only for non-trivial events
  const showRound = event.round && event.type !== "WORKFLOW_STARTED" && event.type !== "WORKFLOW_COMPLETED";

  return (
    <div
      className="sse-event-row"
      style={{ animationDelay: `${index * 20}ms` }}
    >
      {/* Left: icon */}
      <div className="sse-event-icon" style={{ color: meta.color, borderColor: `${meta.color}40` }}>
        <span style={{ fontSize: "0.85rem", lineHeight: 1 }}>{meta.icon}</span>
      </div>

      {/* Right: content */}
      <div className="sse-event-body">
        <div className="sse-event-header">
          <span className="sse-event-type" style={{ color: meta.color }}>
            {meta.label}
          </span>
          {event.agent && event.type !== "WORKFLOW_STARTED" && event.type !== "ROUND_STARTED" && (
            <span className="sse-agent-chip">{event.agent}</span>
          )}
          {showRound && (
            <span className="sse-round-chip">Round {event.round}</span>
          )}
          <span className="sse-event-time">{formatTime(event.timestamp)}</span>
        </div>

        <p className="sse-event-message">{event.message}</p>

        {event.task_name && (
          <div className="sse-event-task">
            <span className="sse-task-label">Task:</span>
            <span className="sse-task-name">{event.task_name}</span>
            {event.status && <TaskStatusBadge status={event.status} size="sm" />}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────
export default function AgentActivityLog({ events = [], connectionStatus = "connecting" }) {
  // Show events newest-first
  const sorted = [...events].reverse();

  return (
    <div className="activity-log-container">
      {/* Header bar */}
      <div className="activity-log-header">
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
            Agent Activity Stream
          </span>
          <span
            style={{
              background: "var(--surface-hover)",
              color: "var(--text-muted)",
              borderRadius: "99px",
              fontSize: "0.7rem",
              fontWeight: 600,
              padding: "1px 8px",
            }}
          >
            {events.length} events
          </span>
        </div>
        <ConnectionPill status={connectionStatus} />
      </div>

      {/* Event feed */}
      {sorted.length === 0 ? (
        <div className="activity-log-empty">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <p>
            {connectionStatus === "connecting"
              ? "Connecting to event stream..."
              : "Waiting for workflow activity. Click Run Supervisor Loop to start."}
          </p>
        </div>
      ) : (
        <div className="sse-event-feed">
          {sorted.map((event, i) => (
            <EventRow key={event.id || `${event.timestamp}-${i}`} event={event} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
