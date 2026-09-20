// src/pages/Onboarding.jsx — New employee onboarding page with pipeline preview and form
import OnboardingForm from "../components/OnboardingForm";

const PIPELINE_AGENTS = [
  {
    role: "SUP",
    name: "Supervisor Agent",
    desc: "Decomposes onboarding goal, evaluates dependency DAG, and coordinates execution.",
  },
  {
    role: "HR",
    name: "HR Specialist Agent",
    desc: "Performs background checks and verifies essential employee documentation.",
  },
  {
    role: "IT",
    name: "IT Infrastructure Agent",
    desc: "Provisions corporate email, SSO credentials, and hardware requisition.",
  },
  {
    role: "FIN",
    name: "Finance & Payroll Agent",
    desc: "Validates bank details, tax withholding, and enrolls in payroll processing.",
  },
  {
    role: "RES",
    name: "Resource Agent",
    desc: "Allocates workstation assets, desk reservation, and security badges.",
  },
];

export default function Onboarding() {
  return (
    <div className="onboarding-page">
      {/* Page Header */}
      <div className="onboarding-page-header">
        <h1>Employee Onboarding</h1>
        <p>
          Register a new team member to initiate the hierarchical multi-agent coordination pipeline.
          The Supervisor Agent automatically orchestrates tasks across specialized agents with real-time dependency tracking.
        </p>
      </div>

      {/* Main Grid: Form + Sidebar Pipeline Info */}
      <div className="onboarding-grid">
        <main>
          <OnboardingForm />
        </main>

        <aside>
          <div className="sidebar-pipeline-card">
            <h3>Agent Pipeline Guide</h3>
            <p>
              Autonomous execution flow triggered upon submission:
            </p>

            <div className="pipeline-flow-diagram">
              {PIPELINE_AGENTS.map((agent, i) => (
                <div key={agent.role}>
                  <div className="pipeline-node">
                    <span className="pipeline-node-role">{agent.role}</span>
                    <div className="pipeline-node-info">
                      <div className="pipeline-node-name">{agent.name}</div>
                      <div className="pipeline-node-desc">{agent.desc}</div>
                    </div>
                  </div>
                  {i < PIPELINE_AGENTS.length - 1 && (
                    <div className="pipeline-connector" aria-hidden="true">
                      ↓
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div
              style={{
                marginTop: "1.25rem",
                paddingTop: "1rem",
                borderTop: "1px solid var(--border)",
                fontSize: "0.75rem",
                color: "var(--text-muted)",
              }}
            >
              Deterministic state machine with automated error handling &amp; retry policies
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
