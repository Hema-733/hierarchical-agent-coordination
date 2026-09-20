// src/pages/WorkflowHistory.jsx — Historical audit trail of all onboarding workflows
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getWorkflows, getWorkflowTasks } from "../api/client";
import TaskStatusBadge from "../components/TaskStatusBadge";

export default function WorkflowHistory() {
  const [workflows, setWorkflows] = useState([]);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await getWorkflows();
        const workflowsList = data || [];
        // Fetch actual tasks for each workflow in parallel to compute accurate completed/total counts
        const enriched = await Promise.all(
          workflowsList.map(async (wf) => {
            try {
              const tasks = await getWorkflowTasks(wf.workflow_id);
              return { ...wf, tasks: Array.isArray(tasks) ? tasks : [] };
            } catch {
              return { ...wf, tasks: [] };
            }
          })
        );
        setWorkflows(enriched);
      } catch (err) {
        setErrorMsg(
          err.response?.data?.detail ||
            err.message ||
            "Unable to retrieve workflow history from backend."
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const filteredWorkflows = workflows.filter((w) => {
    const matchesFilter =
      statusFilter === "ALL" || w.overall_status === statusFilter;
    const term = searchQuery.toLowerCase().trim();
    const matchesSearch =
      !term ||
      w.workflow_id.toLowerCase().includes(term) ||
      w.employee_id.toLowerCase().includes(term);
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="history-page">
      <div className="dashboard-header-row">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <span className="badge badge-primary">Audit Log</span>
          </div>
          <h1>Workflow Historical Records</h1>
          <p>
            Complete audit trail across all completed, paused, and running employee coordination lifecycles.
          </p>
        </div>

        <Link to="/onboarding" className="btn btn-primary btn-sm">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span>New Onboarding</span>
        </Link>
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

      {/* Filters Bar */}
      <div className="dashboard-controls-bar">
        <div className="filter-tabs">
          {["ALL", "COMPLETED", "PAUSED", "FAILED", "RUNNING"].map((tab) => (
            <button
              key={tab}
              type="button"
              className={`filter-tab ${statusFilter === tab ? "active" : ""}`}
              onClick={() => setStatusFilter(tab)}
            >
              {tab}
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

      {/* Audit Table */}
      {isLoading ? (
        <div style={{ textAlign: "center", padding: "4rem 1rem" }}>
          <div className="spinner" style={{ margin: "0 auto 1rem", width: 28, height: 28 }} />
          <p>Loading historical workflows...</p>
        </div>
      ) : filteredWorkflows.length === 0 ? (
        <div className="empty-workflows-panel">
          <h3>No Historical Records</h3>
          <p>There are currently no workflows matching the selected criteria.</p>
        </div>
      ) : (
        <div className="history-table-container">
          <table className="history-table">
            <thead>
              <tr>
                <th>Workflow ID</th>
                <th>Candidate ID</th>
                <th>Status</th>
                <th>Tasks Completed</th>
                <th>Created</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredWorkflows.map((wf) => {
                const safeTasks = Array.isArray(wf.tasks) ? wf.tasks : [];
                const hasTasks = safeTasks.length > 0;
                const total = hasTasks ? safeTasks.length : null;
                const completed = hasTasks
                  ? safeTasks.filter((t) => t.status === "COMPLETED").length
                  : null;

                return (
                  <tr key={wf.workflow_id}>
                    <td>
                      <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600, color: "var(--accent)" }}>
                        {wf.workflow_id}
                      </span>
                    </td>
                    <td>{wf.employee_id}</td>
                    <td>
                      <TaskStatusBadge status={wf.overall_status} size="sm" />
                    </td>
                    <td>
                      {hasTasks ? `${completed} / ${total}` : "—"}
                    </td>
                    <td>
                      {wf.created_at
                        ? new Date(wf.created_at).toLocaleDateString(undefined, {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })
                        : "Recently"}
                    </td>
                    <td>
                      <Link to={`/workflows/${wf.workflow_id}`} className="btn btn-secondary btn-sm">
                        Inspect
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
