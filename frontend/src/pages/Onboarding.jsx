// src/pages/Onboarding.jsx — New employee onboarding page with pipeline preview and form
import OnboardingForm from "../components/OnboardingForm";

const PIPELINE_AGENTS = [
  {
    role: "SUP",
    name: "Supervisor Agent",
    desc: "Dynamically constructs the execution DAG, resolves prerequisite dependencies, and enforces retry policies.",
  },
  {
    role: "HR",
    name: "HR Specialist Agent",
    desc: "Validates document verification compliance, company policies, and generates official offer confirmations.",
  },
  {
    role: "IT",
    name: "IT Infrastructure Agent",
    desc: "Provisions enterprise email accounts, SSO credentials, and hardware asset requisitions.",
  },
  {
    role: "FIN",
    name: "Finance & Payroll Agent",
    desc: "Configures payroll compensation profiles, tax brackets, and initial benefits enrollment.",
  },
  {
    role: "RES",
    name: "Resource Agent",
    desc: "Assigns physical/remote workstation assets, team badge access, and welcome swags.",
  },
];

export default function Onboarding() {
  return (
    <div className="onboarding-page">
      {/* Page Header */}
      <div className="onboarding-page-header">
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
          <span className="badge badge-primary">Phase 15 • Orchestration Engine</span>
        </div>
        <h1>
          Employee <span className="gradient-text">Onboarding Coordination</span>
        </h1>
        <p>
          Register a new team member to trigger the hierarchical autonomous multi-agent pipeline. 
          The Supervisor Agent automatically orchestrates tasks across specialized agents with real-time dependency tracking.
        </p>
      </div>

      {/* Main Grid: Form + Sidebar Pipeline Info */}
      <div className="onboarding-grid">
        <main>
          <OnboardingForm />
        </main>

        <aside>
          <div className="glass-panel sidebar-pipeline-card">
            <h3 style={{ marginBottom: "1rem", fontSize: "1.1rem" }}>
              Coordinated Agent Pipeline
            </h3>
            <p style={{ fontSize: "0.825rem", marginBottom: "1.5rem" }}>
              Upon submission, the Supervisor Agent evaluates dependencies and tasks are distributed:
            </p>

            <div className="pipeline-steps-list">
              {PIPELINE_AGENTS.map((agent, i) => (
                <div key={i} className="pipeline-step-item">
                  <div className="step-agent-icon">{agent.role}</div>
                  <div className="step-details">
                    <div className="step-agent-title">{agent.name}</div>
                    <div className="step-agent-desc">{agent.desc}</div>
                  </div>
                </div>
              ))}
            </div>

            <div
              style={{
                marginTop: "1.5rem",
                paddingTop: "1rem",
                borderTop: "1px solid var(--border-subtle)",
                fontSize: "0.775rem",
                color: "var(--text-muted)",
              }}
            >
              ⚡ Powered by Google Gemini AI &amp; FastAPI Async Coordination
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
