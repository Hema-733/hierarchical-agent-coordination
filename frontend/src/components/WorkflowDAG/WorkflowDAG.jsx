// src/components/WorkflowDAG/WorkflowDAG.jsx
// Interactive SVG DAG canvas for workflow task visualization.
// Consumes tasks[] from polling and sseEvents[] from the existing SSE hook.
// No external graph library. No second event connection.

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { dagLayout } from "./dagLayout.js";
import DagNode from "./DagNode.jsx";
import DagEdge from "./DagEdge.jsx";

// ── SSE event type → task status override ───────────────────────────────────
const SSE_STATUS_MAP = {
  TASK_READY:               "READY",
  AGENT_TASK_STARTED:       "RUNNING",
  AGENT_TASK_COMPLETED:     "COMPLETED",
  TASK_FAILED:              "FAILED",
  TASK_RETRYING:            "READY",
  DOCUMENT_REVIEW_REQUIRED: "PAUSED",
};

// ── Status description for detail panel ────────────────────────────────────
const STATUS_DESC = {
  PENDING:   "Waiting for prerequisites to complete.",
  READY:     "Prerequisites met. Queued for execution.",
  RUNNING:   "Agent is actively executing this task.",
  COMPLETED: "Task finished successfully.",
  FAILED:    "Task failed after exhausting retries.",
  BLOCKED:   "Blocked — a dependency permanently failed.",
  PAUSED:    "Waiting for human document review.",
};

function formatDt(isoStr) {
  if (!isoStr) return null;
  try { return new Date(isoStr).toLocaleString(); }
  catch { return isoStr; }
}

// ── Toolbar button ───────────────────────────────────────────────────────────
function ToolBtn({ onClick, title, children }) {
  return (
    <button
      type="button"
      className="btn btn-secondary btn-sm dag-toolbar-btn"
      onClick={onClick}
      title={title}
      aria-label={title}
    >
      {children}
    </button>
  );
}

// ── Node detail side panel ───────────────────────────────────────────────────
function NodeDetailPanel({ node, onClose, onRetry, actionLoading }) {
  if (!node) return null;

  const statusDesc = STATUS_DESC[node.status] || "";
  const canRetry = node.status === "FAILED";

  return (
    <div className="dag-detail-panel" role="complementary" aria-label="Task detail">
      <div className="dag-detail-header">
        <div>
          <div className="dag-detail-label">Task</div>
          <div className="dag-detail-name">{node.task_name}</div>
        </div>
        <button
          type="button"
          className="dag-detail-close"
          onClick={onClose}
          aria-label="Close detail panel"
        >
          ×
        </button>
      </div>

      <div className="dag-detail-rows">
        <div className="dag-detail-row">
          <span className="dag-detail-key">Agent</span>
          <span className="dag-detail-val">{node.agent}</span>
        </div>
        <div className="dag-detail-row">
          <span className="dag-detail-key">Status</span>
          <span className={`dag-status-chip dag-status-${node.status.toLowerCase()}`}>
            {node.status}
          </span>
        </div>
        {statusDesc && (
          <div className="dag-detail-row dag-detail-desc">
            <span className="dag-detail-val" style={{ color: "var(--text-muted)", fontStyle: "italic" }}>
              {statusDesc}
            </span>
          </div>
        )}
        {node.retry_count > 0 && (
          <div className="dag-detail-row">
            <span className="dag-detail-key">Retries</span>
            <span className="dag-detail-val">{node.retry_count} / {node.max_retries}</span>
          </div>
        )}
        {node.dependencies && node.dependencies.length > 0 && (
          <div className="dag-detail-row">
            <span className="dag-detail-key">Prerequisites</span>
            <span className="dag-detail-val">
              {node.dependencies.join(", ")}
            </span>
          </div>
        )}
        {node.started_at && (
          <div className="dag-detail-row">
            <span className="dag-detail-key">Started</span>
            <span className="dag-detail-val">{formatDt(node.started_at)}</span>
          </div>
        )}
        {node.completed_at && (
          <div className="dag-detail-row">
            <span className="dag-detail-key">Finished</span>
            <span className="dag-detail-val">{formatDt(node.completed_at)}</span>
          </div>
        )}
        {node.error_message && (
          <div className="dag-detail-error">
            <div className="dag-detail-key" style={{ marginBottom: 4 }}>Error</div>
            <div>{node.error_message}</div>
          </div>
        )}
        {node.result && (
          <div className="dag-detail-result">
            <div className="dag-detail-key" style={{ marginBottom: 4 }}>Output</div>
            <pre className="json-pre">{JSON.stringify(node.result, null, 2)}</pre>
          </div>
        )}
      </div>

      {canRetry && (
        <div className="dag-detail-actions">
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => onRetry(node.task_id)}
            disabled={actionLoading}
          >
            {actionLoading ? "Retrying..." : "Retry Task"}
          </button>
        </div>
      )}
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────
export default function WorkflowDAG({ tasks, sseEvents = [], onRetryTask, actionLoading }) {
  const safeTasks = Array.isArray(tasks) ? tasks : [];

  // SSE-derived status overrides: taskName → { status, retryCount }
  const [sseOverrides, setSseOverrides]       = useState(new Map());
  const processedRef                          = useRef(0);

  // Selected node name (for detail panel)
  const [selectedName, setSelectedName]       = useState(null);

  // Hovered node name (for cursor feedback)
  const [hoveredName, setHoveredName]         = useState(null);

  // Current execution round from SSE
  const [currentRound, setCurrentRound]       = useState(null);

  // Pan/zoom
  const [scale, setScale]                     = useState(1);
  const [translate, setTranslate]             = useState({ x: 0, y: 0 });
  const isPanning                             = useRef(false);
  const panStart                              = useRef({ x: 0, y: 0, tx: 0, ty: 0 });
  const svgRef                                = useRef(null);
  const containerRef                          = useRef(null);

  // ── Consume new SSE events incrementally ──────────────────────────────────
  useEffect(() => {
    const newEvents = sseEvents.slice(processedRef.current);
    if (!newEvents.length) return;
    processedRef.current = sseEvents.length;

    setSseOverrides((prev) => {
      const next = new Map(prev);
      for (const evt of newEvents) {
        if (evt.type === "ROUND_STARTED" && evt.round) {
          setCurrentRound(evt.round);
          continue;
        }
        if (evt.type === "WORKFLOW_STARTED") {
          next.clear();
          continue;
        }
        const mapped = SSE_STATUS_MAP[evt.type];
        if (mapped && evt.task_name) {
          next.set(evt.task_name, {
            status:     mapped,
            retryCount: evt.data?.retry_count ?? prev.get(evt.task_name)?.retryCount ?? 0,
          });
        }
      }
      return next;
    });
  }, [sseEvents]);

  // ── Merge SSE overrides into task list ────────────────────────────────────
  const mergedTasks = useMemo(() => {
    return safeTasks.map((t) => {
      const ov = sseOverrides.get(t.task_name);
      if (!ov) return t;
      return {
        ...t,
        status:      ov.status,
        retry_count: ov.retryCount ?? t.retry_count,
      };
    });
  }, [safeTasks, sseOverrides]);

  // ── Compute layout ────────────────────────────────────────────────────────
  const { nodes, edges, svgWidth, svgHeight } = useMemo(
    () => dagLayout(mergedTasks),
    [mergedTasks]
  );

  // ── Fit to container ─────────────────────────────────────────────────────
  const fitToContainer = useCallback(() => {
    const container = containerRef.current;
    if (!container || svgWidth === 0) return;
    const cw = container.clientWidth;
    const ch = container.clientHeight || 300;
    const newScale = Math.min(1, Math.min(cw / svgWidth, ch / svgHeight) * 0.95);
    setScale(newScale);
    setTranslate({ x: 0, y: 0 });
  }, [svgWidth, svgHeight]);

  // Fit on first layout
  useEffect(() => {
    if (nodes.length > 0) fitToContainer();
  }, [nodes.length, fitToContainer]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Zoom controls ─────────────────────────────────────────────────────────
  const zoomIn  = () => setScale((s) => Math.min(2, parseFloat((s + 0.15).toFixed(2))));
  const zoomOut = () => setScale((s) => Math.max(0.3, parseFloat((s - 0.15).toFixed(2))));

  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 0.1 : -0.1;
    setScale((s) => Math.min(2, Math.max(0.3, parseFloat((s + delta).toFixed(2)))));
  };

  // ── Pan controls ──────────────────────────────────────────────────────────
  const handleMouseDown = (e) => {
    if (e.target.closest("g[data-node]")) return; // ignore node clicks
    isPanning.current = true;
    panStart.current = { x: e.clientX, y: e.clientY, tx: translate.x, ty: translate.y };
    e.currentTarget.style.cursor = "grabbing";
  };

  const handleMouseMove = (e) => {
    if (!isPanning.current) return;
    const dx = e.clientX - panStart.current.x;
    const dy = e.clientY - panStart.current.y;
    setTranslate({ x: panStart.current.tx + dx, y: panStart.current.ty + dy });
  };

  const handleMouseUp = (e) => {
    isPanning.current = false;
    e.currentTarget.style.cursor = "grab";
  };

  // ── Node interaction ──────────────────────────────────────────────────────
  const handleNodeClick = (name) => {
    setSelectedName((prev) => (prev === name ? null : name));
  };

  const selectedNode = nodes.find((n) => n.task_name === selectedName) ?? null;

  // ── Completed edge detection ──────────────────────────────────────────────
  const completedNames = new Set(nodes.filter((n) => n.status === "COMPLETED").map((n) => n.task_name));
  const isEdgeCompleted = (edge) =>
    completedNames.has(edge.sourceName) && completedNames.has(edge.targetName);

  // ── Empty state ───────────────────────────────────────────────────────────
  if (nodes.length === 0) {
    return (
      <div className="dag-empty-state">
        <p>No task data available yet.</p>
      </div>
    );
  }

  const canvasHeight = Math.max(280, svgHeight * scale + 40);

  return (
    <div className="dag-outer">
      {/* Toolbar */}
      <div className="dag-toolbar">
        <div className="dag-toolbar-left">
          {currentRound && (
            <span className="dag-round-badge">Round {currentRound}</span>
          )}
        </div>
        <div className="dag-toolbar-right">
          <ToolBtn onClick={fitToContainer} title="Fit to screen">Fit</ToolBtn>
          <ToolBtn onClick={zoomIn}  title="Zoom in">+</ToolBtn>
          <ToolBtn onClick={zoomOut} title="Zoom out">−</ToolBtn>
          <span className="dag-zoom-label">{Math.round(scale * 100)}%</span>
        </div>
      </div>

      {/* Canvas + detail panel layout */}
      <div className="dag-body">
        {/* SVG canvas */}
        <div
          ref={containerRef}
          className="dag-canvas-container"
          style={{ height: canvasHeight }}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <svg
            ref={svgRef}
            width={svgWidth}
            height={svgHeight}
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            style={{
              transform: `translate(${translate.x}px, ${translate.y}px) scale(${scale})`,
              transformOrigin: "top left",
              overflow: "visible",
              cursor: "grab",
              display: "block",
            }}
          >
            {/* Arrowhead marker — defined once */}
            <defs>
              <marker
                id="dag-arrowhead"
                markerWidth="8"
                markerHeight="6"
                refX="7"
                refY="3"
                orient="auto"
              >
                <polygon
                  points="0 0, 8 3, 0 6"
                  fill="var(--border-strong)"
                  opacity="0.7"
                />
              </marker>
              {/* Completed arrowhead */}
              <marker
                id="dag-arrowhead-done"
                markerWidth="8"
                markerHeight="6"
                refX="7"
                refY="3"
                orient="auto"
              >
                <polygon
                  points="0 0, 8 3, 0 6"
                  fill="var(--status-success-border)"
                  opacity="0.8"
                />
              </marker>
            </defs>

            {/* Edges (rendered first, behind nodes) */}
            {edges.map((edge) => (
              <DagEdge
                key={edge.id}
                {...edge}
                completed={isEdgeCompleted(edge)}
              />
            ))}

            {/* Nodes */}
            {nodes.map((node) => (
              <g key={node.task_id} data-node="true">
                <DagNode
                  {...node}
                  selected={selectedName === node.task_name}
                  onClick={() => handleNodeClick(node.task_name)}
                  onHover={setHoveredName}
                />
              </g>
            ))}
          </svg>
        </div>

        {/* Node detail panel */}
        {selectedNode && (
          <NodeDetailPanel
            node={selectedNode}
            onClose={() => setSelectedName(null)}
            onRetry={onRetryTask}
            actionLoading={actionLoading}
          />
        )}
      </div>

      {/* Legend */}
      <div className="dag-legend">
        {[
          { status: "PENDING",   label: "Pending" },
          { status: "READY",     label: "Ready" },
          { status: "RUNNING",   label: "Running" },
          { status: "COMPLETED", label: "Completed" },
          { status: "FAILED",    label: "Failed" },
        ].map(({ status, label }) => (
          <div key={status} className="dag-legend-item">
            <span className={`dag-legend-dot dag-dot-${status.toLowerCase()}`} />
            <span className="dag-legend-label">{label}</span>
          </div>
        ))}
        <div className="dag-legend-item">
          <span className="dag-legend-hint">Click node for details</span>
        </div>
      </div>
    </div>
  );
}
