// src/components/WorkflowDAG/DagNode.jsx
// SVG task node — rounded rect with task name, agent, status indicator.

import { NODE_WIDTH, NODE_HEIGHT } from "./dagLayout.js";

// ── Status visual tokens ────────────────────────────────────────────────────
const STATUS_STYLE = {
  PENDING: {
    fill:          "var(--surface)",
    stroke:        "var(--border)",
    strokeWidth:   1,
    labelColor:    "var(--text-muted)",
    agentColor:    "var(--text-muted)",
    dotColor:      "var(--text-muted)",
    dash:          "none",
  },
  READY: {
    fill:          "var(--accent-subtle)",
    stroke:        "var(--accent)",
    strokeWidth:   1.5,
    labelColor:    "var(--accent)",
    agentColor:    "var(--text-secondary)",
    dotColor:      "var(--accent)",
    dash:          "none",
  },
  RUNNING: {
    fill:          "var(--accent-subtle)",
    stroke:        "var(--accent)",
    strokeWidth:   1.5,
    labelColor:    "var(--text-primary)",
    agentColor:    "var(--text-secondary)",
    dotColor:      "var(--accent)",
    dash:          "none",
  },
  COMPLETED: {
    fill:          "var(--status-success-bg)",
    stroke:        "var(--status-success-border)",
    strokeWidth:   1.5,
    labelColor:    "var(--status-success)",
    agentColor:    "var(--text-muted)",
    dotColor:      "var(--status-success)",
    dash:          "none",
  },
  FAILED: {
    fill:          "var(--status-danger-bg)",
    stroke:        "var(--status-danger-border)",
    strokeWidth:   1.5,
    labelColor:    "var(--status-danger)",
    agentColor:    "var(--text-muted)",
    dotColor:      "var(--status-danger)",
    dash:          "none",
  },
  BLOCKED: {
    fill:          "var(--surface)",
    stroke:        "var(--border)",
    strokeWidth:   1,
    labelColor:    "var(--text-muted)",
    agentColor:    "var(--text-muted)",
    dotColor:      "var(--text-muted)",
    dash:          "4 3",
  },
  PAUSED: {
    fill:          "var(--status-warning-bg)",
    stroke:        "var(--status-warning-border)",
    strokeWidth:   1.5,
    labelColor:    "var(--status-warning)",
    agentColor:    "var(--text-muted)",
    dotColor:      "var(--status-warning)",
    dash:          "none",
  },
};

// Short agent abbreviations shown on the node chip
const AGENT_SHORT = {
  "HR Agent":               "HR",
  "IT Agent":               "IT",
  "Finance Agent":          "FIN",
  "Resource / Admin Agent": "RES",
  "Supervisor Agent":       "SUP",
};

function truncate(str, maxLen) {
  if (!str) return "";
  return str.length > maxLen ? str.slice(0, maxLen - 1) + "\u2026" : str;
}

/**
 * DagNode — renders a single task as an SVG group.
 *
 * Props:
 *   task_id, task_name, agent, status, retry_count — task data
 *   x, y   — top-left position (from dagLayout)
 *   selected — bool
 *   onClick  — fn
 *   onHover  — fn(task_name | null)
 */
export default function DagNode({
  task_id,
  task_name,
  agent,
  status,
  retry_count,
  x,
  y,
  selected,
  onClick,
  onHover,
}) {
  const s = STATUS_STYLE[status] || STATUS_STYLE.PENDING;
  const shortAgent = AGENT_SHORT[agent] || (agent ? agent.split(" ")[0] : "?");
  const radius = 6;

  // Highlight ring on selection
  const selectionRing = selected ? (
    <rect
      x={x - 3}
      y={y - 3}
      width={NODE_WIDTH + 6}
      height={NODE_HEIGHT + 6}
      rx={radius + 3}
      ry={radius + 3}
      fill="none"
      stroke="var(--accent)"
      strokeWidth={2}
      opacity={0.35}
    />
  ) : null;

  // Running indicator: small pulsing dot (animated via CSS in App.css)
  const runningDot = (status === "RUNNING") ? (
    <circle
      cx={x + NODE_WIDTH - 12}
      cy={y + 12}
      r={4}
      fill="var(--accent)"
      className="dag-running-dot"
    />
  ) : null;

  // Status icon in top-right corner for non-running states
  const statusIcon = (() => {
    if (status === "COMPLETED") {
      return (
        <text
          x={x + NODE_WIDTH - 10}
          y={y + 16}
          textAnchor="middle"
          fontSize="10"
          fill="var(--status-success)"
        >
          ✓
        </text>
      );
    }
    if (status === "FAILED") {
      return (
        <text
          x={x + NODE_WIDTH - 10}
          y={y + 16}
          textAnchor="middle"
          fontSize="10"
          fill="var(--status-danger)"
        >
          ✕
        </text>
      );
    }
    return null;
  })();

  // Retry badge (bottom-right)
  const retryBadge = retry_count > 0 ? (
    <g>
      <rect
        x={x + NODE_WIDTH - 38}
        y={y + NODE_HEIGHT - 18}
        width={34}
        height={14}
        rx={3}
        fill="var(--status-warning-bg)"
        stroke="var(--status-warning-border)"
        strokeWidth={0.75}
      />
      <text
        x={x + NODE_WIDTH - 21}
        y={y + NODE_HEIGHT - 8}
        textAnchor="middle"
        fontSize="8.5"
        fontWeight="600"
        fill="var(--status-warning)"
        fontFamily="var(--font-mono)"
      >
        {`↺ ${retry_count}`}
      </text>
    </g>
  ) : null;

  // Agent chip (bottom-left)
  const agentChip = (
    <g>
      <rect
        x={x + 8}
        y={y + NODE_HEIGHT - 18}
        width={28}
        height={14}
        rx={3}
        fill="var(--surface-hover)"
        stroke="var(--border)"
        strokeWidth={0.75}
      />
      <text
        x={x + 22}
        y={y + NODE_HEIGHT - 8}
        textAnchor="middle"
        fontSize="8"
        fontWeight="700"
        fill="var(--text-muted)"
        fontFamily="var(--font-mono)"
        letterSpacing="0.04em"
      >
        {shortAgent}
      </text>
    </g>
  );

  return (
    <g
      onClick={onClick}
      onMouseEnter={() => onHover && onHover(task_name)}
      onMouseLeave={() => onHover && onHover(null)}
      style={{ cursor: "pointer" }}
    >
      {selectionRing}

      {/* Main node rect */}
      <rect
        x={x}
        y={y}
        width={NODE_WIDTH}
        height={NODE_HEIGHT}
        rx={radius}
        ry={radius}
        fill={s.fill}
        stroke={s.stroke}
        strokeWidth={s.strokeWidth}
        strokeDasharray={s.dash}
        style={{ transition: "fill 0.3s ease, stroke 0.3s ease" }}
      />

      {/* Task name */}
      <text
        x={x + 12}
        y={y + 26}
        fontSize="12"
        fontWeight="600"
        fill={s.labelColor}
        fontFamily="var(--font-sans)"
        style={{ transition: "fill 0.3s ease", userSelect: "none" }}
      >
        {truncate(task_name, 20)}
      </text>

      {/* Agent label */}
      <text
        x={x + 12}
        y={y + 42}
        fontSize="10"
        fill={s.agentColor}
        fontFamily="var(--font-sans)"
        style={{ userSelect: "none" }}
      >
        {truncate(agent, 24)}
      </text>

      {agentChip}
      {retryBadge}
      {runningDot}
      {statusIcon}
    </g>
  );
}
