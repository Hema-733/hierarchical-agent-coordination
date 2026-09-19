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
} from "../api/client";
import TaskStatusBadge from "../components/TaskStatusBadge";
import AgentActivityLog from "../components/AgentActivityLog";

export default function WorkflowDetail() {
  const { id: workflowId } = useParams();

  const [workflow, setWorkflow] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [aiSummary, setAiSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [activeTab, setActiveTab] = useState("TASKS"); // 'TASKS' or 'LOGS'

  const loadWorkflowData = useCallback(async () => {
    try {
      const wf = await getWorkflowById(workflowId);
      setWorkflow(wf);
      setTasks(wf.tasks || []);
      setErrorMsg(null);
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

    const fetchAll = async () => {
      try {
        const wf = await getWorkflowById(workflowId);
        if (isSubscribed) {
          setWorkflow(wf);
          setTasks(wf.tasks || []);
          setErrorMsg(null);
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

      try {
        const aiData = await getAIWorkflowSummary(workflowId);
        if (isSubscribed) {
          setAiSummary(aiData);
        }
      } catch {
        // AI narrative fallback
      }
    };

    fetchAll();

    const interval = setInterval(fetchAll, 4000);
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
      await retryTask(taskId);
      await loadWorkflowData();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to retry task.");
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

      {/* Main Workflow Header Card */}
      <div className="glass-panel detail-header-panel">
        <div className="detail-header-top">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
              <TaskStatusBadge status={workflow?.overall_status} />
              <span className="badge badge-primary">DAG Pipeline</span>
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
        <div className="glass-panel ai-summary-card">
          <div className="ai-summary-badge">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
            <span>Gemini AI Executive Narrative</span>
          </div>
          <p className="ai-summary-text">{aiSummary.ai_summary || aiSummary.summary}</p>
        </div>
      )}

      {/* Detail Tabs: DAG Task Execution vs Agent Activity Log */}
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
          className={`detail-tab ${activeTab === "LOGS" ? "active" : ""}`}
          onClick={() => setActiveTab("LOGS")}
        >
          Agent Live Audit Trail
        </button>
      </div>

      {/* Tab 1: Task Execution DAG Tree */}
      {activeTab === "TASKS" && (
        <div className="task-tree-container">
          {tasks.map((task, index) => (
            <div key={task.task_id} className="glass-panel task-node-card">
              <div className="task-node-header">
                <div className="task-node-index">{index + 1}</div>
                <div className="task-node-title-group">
                  <h3>{task.task_name}</h3>
                  <div className="task-node-agent">
                    Assigned Agent: <strong>{task.agent}</strong>
                  </div>
                </div>

                <div className="task-node-status">
                  {task.retry_count > 0 && (
                    <span className="badge badge-warning" style={{ fontSize: "0.75rem" }}>
                      Retry {task.retry_count}/{task.max_retries}
                    </span>
                  )}
                  <TaskStatusBadge status={task.status} />
                  {task.status === "FAILED" && (
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleRetryTask(task.task_id)}
                      disabled={actionLoading}
                    >
                      Retry
                    </button>
                  )}
                </div>
              </div>

              {/* Task Dependencies */}
              {task.dependencies && task.dependencies.length > 0 && (
                <div className="task-deps-row">
                  <span className="deps-label">Prerequisites:</span>
                  {task.dependencies.map((dep, dIdx) => (
                    <span key={dIdx} className="dep-pill">
                      {dep}
                    </span>
                  ))}
                </div>
              )}

              {/* Error Message banner if failed */}
              {task.error_message && (
                <div className="task-error-text">
                  <strong>Failure: </strong> {task.error_message}
                </div>
              )}

              {/* Task Output Data if completed */}
              {task.result && (
                <div className="task-result-box">
                  <div className="payload-label">Task Artifact Data:</div>
                  <pre className="json-pre">{JSON.stringify(task.result, null, 2)}</pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Tab 2: Embedded Agent Activity Log */}
      {activeTab === "LOGS" && (
        <div style={{ marginTop: "1rem" }}>
          <AgentActivityLog tasks={tasks} />
        </div>
      )}
    </div>
  );
}
