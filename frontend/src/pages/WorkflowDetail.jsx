// src/pages/WorkflowDetail.jsx — Deep inspection of workflow DAG, agent task states, AI summary, and controls
import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import {
  getWorkflowById,
  executeWorkflow,
  pauseWorkflow,
  resumeWorkflow,
  retryTask,
  getAIWorkflowSummary,
  getEmployeeById,
  updateEmployeeDocuments,
} from "../api/client";
import { useWorkflowStream } from "../api/useWorkflowStream";
import TaskStatusBadge from "../components/TaskStatusBadge";
import AgentActivityLog from "../components/AgentActivityLog";
import WorkflowDAG from "../components/WorkflowDAG";
import DocumentReviewPanel from "../components/DocumentReviewPanel";

export default function WorkflowDetail() {
  const { id: workflowId } = useParams();

  const [workflow, setWorkflow] = useState(null);
  const [employee, setEmployee] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [aiSummary, setAiSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [activeTab, setActiveTab] = useState("TASKS"); // 'TASKS', 'DOCUMENTS', or 'LOGS'

  // ── Real-time SSE stream ──
  const { events: sseEvents, connectionStatus } = useWorkflowStream(workflowId, !!workflowId);

  const loadWorkflowData = useCallback(async () => {
    try {
      const wf = await getWorkflowById(workflowId);
      setWorkflow(wf);
      setTasks(wf.tasks || []);
      setErrorMsg(null);

      if (wf.employee_id) {
        try {
          const emp = await getEmployeeById(wf.employee_id);
          setEmployee(emp);
        } catch {
          // Ignore employee fetch error if not yet created
        }
      }
    } catch (err) {
      setErrorMsg(
        err.response?.data?.detail ||
          err.message ||
          "Failed to fetch workflow details from server."
      );
    } finally {
      setIsLoading(false);
    }
  }, [workflowId]);

  const loadAiNarrative = useCallback(async () => {
    try {
      const aiData = await getAIWorkflowSummary(workflowId);
      setAiSummary(aiData);
    } catch {
      // Gracefully continue without AI summary if service is offline
    }
  }, [workflowId]);

  useEffect(() => {
    let isSubscribed = true;
    let hasLoadedAi = false;

    // Fetch AI summary once, when the workflow is in a terminal state
    const fetchAiIfTerminal = async (status) => {
      if (hasLoadedAi) return;
      if (status !== "COMPLETED" && status !== "FAILED") return;
      try {
        const aiData = await getAIWorkflowSummary(workflowId);
        if (isSubscribed) {
          setAiSummary(aiData);
          hasLoadedAi = true;
        }
      } catch {
        // Gracefully continue without AI summary
      }
    };

    const fetchAll = async () => {
      try {
        const wf = await getWorkflowById(workflowId);
        if (isSubscribed) {
          setWorkflow(wf);
          setTasks(wf.tasks || []);
          setErrorMsg(null);

          if (wf.employee_id) {
            try {
              const emp = await getEmployeeById(wf.employee_id);
              if (isSubscribed) setEmployee(emp);
            } catch {
              // Ignore
            }
          }

          // Fetch AI summary once when workflow reaches a terminal state
          await fetchAiIfTerminal(wf.overall_status);
        }
      } catch (err) {
        if (isSubscribed) {
          setErrorMsg(
            err.response?.data?.detail ||
              err.message ||
              "Failed to fetch workflow details from server."
          );
        }
      } finally {
        if (isSubscribed) {
          setIsLoading(false);
        }
      }
    };

    fetchAll();
    const interval = setInterval(fetchAll, 3500);
    return () => {
      isSubscribed = false;
      clearInterval(interval);
    };
  }, [workflowId]);

  // Actions
  const handleExecute = async () => {
    setActionLoading(true);
    try {
      await executeWorkflow(workflowId);
      await loadWorkflowData();
      await loadAiNarrative();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Execution failed.");
    } finally {
      setActionLoading(false);
    }
  };

  const handlePause = async () => {
    setActionLoading(true);
    try {
      await pauseWorkflow(workflowId, "Paused manually by operator");
      await loadWorkflowData();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to pause workflow.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    setActionLoading(true);
    try {
      await resumeWorkflow(workflowId);
      await loadWorkflowData();
      await loadAiNarrative();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to resume workflow.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRetryTask = async (taskId) => {
    setActionLoading(true);
    try {
      // Re-queue the failed/paused task as READY
      await retryTask(taskId);
      // Automatically re-trigger the Supervisor so it picks up the re-queued task
      await executeWorkflow(workflowId);
      await loadWorkflowData();
      await loadAiNarrative();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to retry task.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateDocument = async (docKey, patchData, autoResume = true) => {
    if (!workflow?.employee_id) return;
    setActionLoading(true);
    try {
      const payload = {
        [docKey]: patchData,
        workflow_id: workflowId,
        auto_resume: autoResume,
      };
      const updatedEmp = await updateEmployeeDocuments(workflow.employee_id, payload);
      setEmployee(updatedEmp);
      await loadWorkflowData();
      await loadAiNarrative();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to update document status.");
    } finally {
      setActionLoading(false);
    }
  };

  if (isLoading && !workflow) {
    return (
      <div style={{ textAlign: "center", padding: "5rem 1rem" }}>
        <div className="spinner" style={{ margin: "0 auto 1.5rem", width: 32, height: 32 }} />
        <p>Inspecting workflow and agent task dependencies...</p>
      </div>
    );
  }

  const completedCount = tasks.filter((t) => t.status === "COMPLETED").length;
  const progressPct = tasks.length > 0 ? Math.round((completedCount / tasks.length) * 100) : 0;

  // Document review status summary
  const docs = employee?.documents || {};
  const docList = Object.values(docs);
  const pendingReviewCount = docList.filter(
    (d) => d && (d.status === "MISSING" || d.status === "REJECTED" || d.status === "UNDER_REVIEW")
  ).length;

  const isWorkflowPaused = workflow?.overall_status === "PAUSED";

  return (
    <div className="workflow-detail-page">
      {/* Navigation Breadcrumb */}
      <div className="detail-breadcrumb">
        <Link to="/" className="breadcrumb-link">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          <span>Dashboard</span>
        </Link>
        <span className="breadcrumb-sep">/</span>
        <span className="breadcrumb-curr">{workflowId}</span>
      </div>

      {errorMsg && (
        <div className="alert-box alert-danger">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <div>{errorMsg}</div>
        </div>
      )}

      {/* Human-in-the-Loop Action Required Banner */}
      {isWorkflowPaused && (
        <div className="hitl-action-banner">
          <div className="hitl-action-left">
            <svg className="hitl-action-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <div>
              <div className="hitl-action-title">Action Required: Human-in-the-Loop Review Needed</div>
              <div className="hitl-action-desc">
                {workflow?.paused_reason || workflow?.error_message || "Workflow coordination is paused awaiting manual document verification or review."}
              </div>
            </div>
          </div>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <button
              type="button"
              className="btn btn-sm btn-primary"
              onClick={() => setActiveTab("DOCUMENTS")}
            >
              Review Documents
            </button>
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={handleResume}
              disabled={actionLoading}
            >
              {actionLoading ? "Resuming..." : "Resume Pipeline"}
            </button>
          </div>
        </div>
      )}

      {/* Main Workflow Header Card */}
      <div className="detail-header-panel">
        <div className="detail-header-top">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
              <TaskStatusBadge status={workflow?.overall_status} />
              <span className="badge badge-neutral">Pipeline</span>
            </div>
            <h1>{workflowId}</h1>
            <div className="detail-meta-text">
              <span>Candidate: <strong>{workflow?.employee_id}</strong></span>
              <span>•</span>
              <span>
                Created: {workflow?.created_at ? new Date(workflow.created_at).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                }) : "Recently"}
              </span>
            </div>
          </div>

          {/* Supervisor Action Controls */}
          <div className="detail-controls-group">
            {workflow?.overall_status === "PAUSED" ? (
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleResume}
                disabled={actionLoading}
              >
                {actionLoading ? "Resuming..." : "Resume Workflow"}
              </button>
            ) : workflow?.overall_status === "RUNNING" ? (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handlePause}
                disabled={actionLoading}
              >
                {actionLoading ? "Pausing..." : "Pause Workflow"}
              </button>
            ) : workflow?.overall_status === "PENDING" ? (
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleExecute}
                disabled={actionLoading}
              >
                {actionLoading ? "Starting..." : "Run Supervisor Loop"}
              </button>
            ) : null}

            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={loadWorkflowData}
              disabled={actionLoading}
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Progress bar inside header */}
        <div style={{ marginTop: "1.5rem" }}>
          <div className="progress-labels">
            <span>Orchestration Progress</span>
            <span className="progress-count">
              {completedCount} / {tasks.length} tasks completed ({progressPct}%)
            </span>
          </div>
          <div className="progress-track" style={{ height: "8px" }}>
            <div className="progress-fill" style={{ width: `${progressPct}%` }} />
          </div>
        </div>
      </div>

      {/* AI Narrative Executive Summary Card */}
      {(aiSummary?.ai_summary || aiSummary?.summary) && (
        <div className="card ai-summary-card">
          <div className="ai-summary-badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
            <span>Executive Status Summary</span>
          </div>
          <p className="ai-summary-text">{aiSummary.ai_summary || aiSummary.summary}</p>
        </div>
      )}

      {/* Detail Tabs: DAG vs Documents vs Activity Log */}
      <div className="detail-tabs-bar">
        <button
          type="button"
          className={`detail-tab ${activeTab === "TASKS" ? "active" : ""}`}
          onClick={() => setActiveTab("TASKS")}
        >
          Task Dependency Graph ({tasks.length})
        </button>
        <button
          type="button"
          className={`detail-tab ${activeTab === "DOCUMENTS" ? "active" : ""}`}
          onClick={() => setActiveTab("DOCUMENTS")}
        >
          Candidate Documents (4)
          {pendingReviewCount > 0 && (
            <span
              style={{
                marginLeft: "6px",
                background: isWorkflowPaused ? "var(--status-warning)" : "var(--status-neutral)",
                color: "#fff",
                borderRadius: "99px",
                fontSize: "0.65rem",
                fontWeight: 700,
                padding: "1px 6px",
              }}
            >
              {pendingReviewCount} pending
            </span>
          )}
        </button>
        <button
          type="button"
          className={`detail-tab ${activeTab === "LOGS" ? "active" : ""}`}
          onClick={() => setActiveTab("LOGS")}
        >
          Agent Live Audit Trail
          {sseEvents.length > 0 && (
            <span
              style={{
                marginLeft: "6px",
                background: "var(--accent)",
                color: "#fff",
                borderRadius: "99px",
                fontSize: "0.65rem",
                fontWeight: 700,
                padding: "1px 6px",
              }}
            >
              {sseEvents.length}
            </span>
          )}
        </button>
      </div>

      {/* Tab 1: Interactive Visual DAG */}
      {activeTab === "TASKS" && (
        <WorkflowDAG
          tasks={tasks}
          sseEvents={sseEvents}
          onRetryTask={handleRetryTask}
          actionLoading={actionLoading}
        />
      )}

      {/* Tab 2: Human-in-the-Loop Document Verification Panel */}
      {activeTab === "DOCUMENTS" && (
        <DocumentReviewPanel
          employee={employee}
          workflow={workflow}
          onUpdateDocument={handleUpdateDocument}
          actionLoading={actionLoading}
        />
      )}

      {/* Tab 3: Real-time SSE Agent Activity Log */}
      {activeTab === "LOGS" && (
        <div style={{ marginTop: "1rem" }}>
          <AgentActivityLog events={sseEvents} connectionStatus={connectionStatus} />
        </div>
      )}
    </div>
  );
}
