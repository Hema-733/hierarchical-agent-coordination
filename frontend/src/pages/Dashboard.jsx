// src/pages/Dashboard.jsx — Live operations dashboard with metrics, status filters, and workflow cards
import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { getWorkflows } from "../api/client";
import WorkflowCard from "../components/WorkflowCard";

export default function Dashboard() {
  const [workflows, setWorkflows] = useState([]);
  const [activeFilter, setActiveFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchWorkflowData = useCallback(async () => {
    try {
      const data = await getWorkflows();
      setWorkflows(data || []);
      setErrorMsg(null);
    } catch (err) {
      setErrorMsg(
        err.response?.data?.detail ||
          err.message ||
          "Unable to connect to backend service. Please ensure the server is active."
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isSubscribed = true;

    const load = async () => {
      try {
        const data = await getWorkflows();
        if (isSubscribed) {
          setWorkflows(data || []);
          setErrorMsg(null);
        }
      } catch (err) {
        if (isSubscribed) {
          setErrorMsg(
            err.response?.data?.detail ||
              err.message ||
              "Unable to connect to backend service. Please ensure the server is active."
          );
        }
      } finally {
        if (isSubscribed) {
          setIsLoading(false);
        }
      }
    };

    load();
    let timer = null;
    if (autoRefresh) {
      timer = setInterval(load, 5000);
    }
    return () => {
      isSubscribed = false;
      if (timer) clearInterval(timer);
    };
  }, [autoRefresh]);

  // Compute aggregate statistics
  const totalCount = workflows.length;
  const runningCount = workflows.filter(
    (w) => w.overall_status === "RUNNING" || w.overall_status === "READY"
  ).length;
  const pausedCount = workflows.filter((w) => w.overall_status === "PAUSED").length;
  const completedCount = workflows.filter((w) => w.overall_status === "COMPLETED").length;
  const failedCount = workflows.filter((w) => w.overall_status === "FAILED").length;

  // Filter workflows by selected tab and search term
  const filteredWorkflows = workflows.filter((w) => {
    const matchesFilter =
      activeFilter === "ALL" ||
      (activeFilter === "RUNNING" && (w.overall_status === "RUNNING" || w.overall_status === "READY")) ||
      w.overall_status === activeFilter;

    const term = searchQuery.toLowerCase().trim();
    const matchesSearch =
      !term ||
      w.workflow_id.toLowerCase().includes(term) ||
      w.employee_id.toLowerCase().includes(term);

    return matchesFilter && matchesSearch;
  });

  return (
    <div className="dashboard-page">
      {/* Dashboard Top Header */}
      <div className="dashboard-header-row">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            {autoRefresh && (
              <span className="badge badge-success" style={{ fontSize: "0.7rem" }}>
                <span className="pulse-active" style={{ width: 6, height: 6 }} />
                Live Sync (5s)
              </span>
            )}
          </div>
          <h1>Orchestration Dashboard</h1>
          <p>
            Monitor hierarchical multi-agent workflows, active task DAGs, and autonomous handoffs.
          </p>
        </div>

        <div className="dashboard-actions">
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setAutoRefresh((prev) => !prev)}
          >
            {autoRefresh ? "Pause Live Sync" : "Enable Live Sync"}
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={fetchWorkflowData}
            disabled={isLoading}
          >
            Refresh
          </button>
          <Link to="/onboarding" className="btn btn-primary btn-sm">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span>New Onboarding</span>
          </Link>
        </div>
      </div>

      {errorMsg && (
        <div className="alert-box alert-danger" style={{ marginTop: "1rem" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <div>{errorMsg}</div>
        </div>
      )}

      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card" onClick={() => setActiveFilter("ALL")}>
          <div className="metric-label">Total Workflows</div>
          <div className="metric-val">{totalCount}</div>
          <div className="metric-hint">All instantiated DAG pipelines</div>
        </div>

        <div className="metric-card" onClick={() => setActiveFilter("RUNNING")}>
          <div className="metric-label">In Progress</div>
          <div className="metric-val" style={{ color: "var(--accent)" }}>{runningCount}</div>
          <div className="metric-hint">Active multi-agent execution</div>
        </div>

        <div className="metric-card" onClick={() => setActiveFilter("PAUSED")}>
          <div className="metric-label">Paused / Needs Info</div>
          <div className="metric-val" style={{ color: "var(--status-warning)" }}>{pausedCount}</div>
          <div className="metric-hint">Awaiting documents or input</div>
        </div>

        <div className="metric-card" onClick={() => setActiveFilter("COMPLETED")}>
          <div className="metric-label">Completed</div>
          <div className="metric-val" style={{ color: "var(--status-success)" }}>{completedCount}</div>
          <div className="metric-hint">Successfully provisioned</div>
        </div>
      </div>

      {/* Controls Bar: Search & Status Filters */}
      <div className="dashboard-controls-bar">
        <div className="filter-tabs">
          {["ALL", "RUNNING", "PAUSED", "COMPLETED", "FAILED"].map((tab) => (
            <button
              key={tab}
              type="button"
              className={`filter-tab ${activeFilter === tab ? "active" : ""}`}
              onClick={() => setActiveFilter(tab)}
            >
              {tab}
              {tab === "FAILED" && failedCount > 0 && (
                <span className="tab-pill-alert">{failedCount}</span>
              )}
            </button>
          ))}
        </div>

        <div className="search-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            className="search-input"
            placeholder="Search by Workflow or Candidate ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Workflows Grid Area */}
      {isLoading && workflows.length === 0 ? (
        <div style={{ textAlign: "center", padding: "4rem 1rem" }}>
          <div className="spinner" style={{ margin: "0 auto 1rem", width: 28, height: 28 }} />
          <p>Syncing workflow states from supervisor...</p>
        </div>
      ) : filteredWorkflows.length === 0 ? (
        <div className="empty-workflows-panel">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
            <line x1="8" y1="21" x2="16" y2="21" />
            <line x1="12" y1="17" x2="12" y2="21" />
          </svg>
          <h3>No Workflows Found</h3>
          <p>
            {searchQuery || activeFilter !== "ALL"
              ? "No workflows match your current search or status filter."
              : "No onboarding workflows have been initiated yet."}
          </p>
          <Link to="/onboarding" className="btn btn-primary" style={{ marginTop: "1rem" }}>
            Create First Onboarding Workflow
          </Link>
        </div>
      ) : (
        <div className="workflows-grid">
          {filteredWorkflows.map((wf) => (
            <WorkflowCard key={wf.workflow_id} workflow={wf} />
          ))}
        </div>
      )}
    </div>
  );
}
