// src/components/WorkflowDAG/DagEdge.jsx
// SVG directed edge connecting two task nodes with a cubic bezier curve.

/**
 * DagEdge renders a single dependency arrow between two nodes.
 *
 * Props:
 *   id          string   unique edge key
 *   x1, y1      number   source point (center-right of source node)
 *   cx1, cy1    number   bezier control point 1
 *   cx2, cy2    number   bezier control point 2
 *   x2, y2      number   target point (center-left of target node)
 *   completed   bool     true if both source and target are COMPLETED
 */
export default function DagEdge({ id, x1, y1, cx1, cy1, cx2, cy2, x2, y2, completed }) {
  const stroke = completed ? "var(--status-success-border)" : "var(--border-strong)";
  const opacity = completed ? 0.9 : 0.6;

  return (
    <path
      key={id}
      d={`M ${x1} ${y1} C ${cx1} ${cy1} ${cx2} ${cy2} ${x2} ${y2}`}
      stroke={stroke}
      strokeWidth={completed ? 1.5 : 1}
      fill="none"
      opacity={opacity}
      markerEnd="url(#dag-arrowhead)"
      style={{ transition: "stroke 0.4s ease, opacity 0.4s ease" }}
    />
  );
}
