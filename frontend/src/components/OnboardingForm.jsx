// src/components/OnboardingForm.jsx — Minimalist Enterprise Onboarding Initiation Form
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { submitOnboarding } from "../api/client";

const INITIAL_FORM_STATE = {
  employee_name: "",
  email: "",
  phone: "",
  department: "Engineering",
  designation: "Software Engineer",
  joining_date: new Date().toISOString().split("T")[0],
  manager: "Sarah Connor (VP Eng)",
  documents: {
    id_proof_submitted: true,
    address_proof_submitted: true,
    bank_details_submitted: true,
    education_certs_submitted: true,
  },
};

const PRESETS = [
  {
    label: "Demo: Software Engineer",
    data: {
      employee_name: "Alex Rivera",
      email: "alex.rivera@techcorp.io",
      phone: "+1-555-019-2834",
      department: "Engineering",
      designation: "Senior Frontend Engineer",
      joining_date: new Date().toISOString().split("T")[0],
      manager: "Elena Rostova (Director)",
      documents: {
        id_proof_submitted: true,
        address_proof_submitted: true,
        bank_details_submitted: true,
        education_certs_submitted: true,
      },
    },
  },
  {
    label: "Demo: Financial Analyst",
    data: {
      employee_name: "David Sterling",
      email: "david.sterling@techcorp.io",
      phone: "+1-555-014-9821",
      department: "Finance",
      designation: "Senior Financial Analyst",
      joining_date: new Date().toISOString().split("T")[0],
      manager: "Marcus Vance (CFO)",
      documents: {
        id_proof_submitted: true,
        address_proof_submitted: true,
        bank_details_submitted: false, // Demonstrates paused/retry workflow
        education_certs_submitted: true,
      },
    },
  },
];

export default function OnboardingForm() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState(INITIAL_FORM_STATE);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successResponse, setSuccessResponse] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleDocToggle = (key) => {
    setFormData((prev) => ({
      ...prev,
      documents: {
        ...prev.documents,
        [key]: !prev.documents[key],
      },
    }));
  };

  const handleKeyDown = (e, key) => {
    if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      handleDocToggle(key);
    }
  };

  const applyPreset = (preset) => {
    setFormData(preset.data);
    setErrorMsg(null);
  };

  const resetForm = () => {
    setFormData(INITIAL_FORM_STATE);
    setSuccessResponse(null);
    setErrorMsg(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);

    // Basic frontend validation
    if (!formData.employee_name.trim() || formData.employee_name.length < 2) {
      setErrorMsg("Please enter a valid employee name (minimum 2 characters).");
      return;
    }
    if (!formData.email.includes("@")) {
      setErrorMsg("Please provide a valid corporate email address.");
      return;
    }
    if (!formData.phone.trim() || formData.phone.length < 10) {
      setErrorMsg("Please enter a valid contact phone number (at least 10 digits).");
      return;
    }

    setIsLoading(true);

    try {
      const response = await submitOnboarding(formData);
      setSuccessResponse(response);
    } catch (err) {
      const detail =
        err.response?.data?.detail ||
        err.message ||
        "Failed to submit onboarding request. Make sure the backend server is running.";
      setErrorMsg(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setIsLoading(false);
    }
  };

  // Render Confirmation / Success view
  if (successResponse) {
    const { employee, workflow } = successResponse;
    return (
      <div className="card form-card success-card">
        <div className="success-icon-badge" aria-hidden="true">
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>

        <h2>Onboarding Initiated</h2>
        <p>
          The Supervisor Agent has orchestrated tasks across HR, IT, Finance, and Resource Agents.
        </p>

        <div className="success-meta-grid">
          <div className="meta-box">
            <div className="meta-label">Employee ID</div>
            <div className="meta-val">{employee.employee_id}</div>
          </div>
          <div className="meta-box">
            <div className="meta-label">Workflow ID</div>
            <div className="meta-val">{workflow.workflow_id}</div>
          </div>
          <div className="meta-box">
            <div className="meta-label">Candidate Name</div>
            <div className="meta-val">{employee.employee_name}</div>
          </div>
          <div className="meta-box">
            <div className="meta-label">Initial Status</div>
            <div className="meta-val">
              <span className="badge badge-primary">{workflow.overall_status || workflow.status}</span>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", justifyContent: "center" }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => navigate(`/workflows/${workflow.workflow_id}`)}
          >
            Track Workflow Execution
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={resetForm}
          >
            Onboard Another Employee
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="form-card">
      {/* Header bar with quick-fill presets */}
      <div className="form-header-bar">
        <div>
          <h2>Employee Registration</h2>
          <p>
            Enter new hire credentials to instantiate the autonomous workflow pipeline.
          </p>
        </div>
        <div className="quick-fill-group">
          <span className="quick-fill-label">Quick Fill:</span>
          {PRESETS.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              className="quick-fill-btn"
              onClick={() => applyPreset(preset)}
              disabled={isLoading}
            >
              {preset.label.replace("Demo: ", "")}
            </button>
          ))}
        </div>
      </div>

      {errorMsg && (
        <div className="alert-box alert-danger" role="alert">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <div>{errorMsg}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        {/* Section 1: Personal Information */}
        <div className="form-section">
          <div className="form-section-title">
            <span>1. Personal Information</span>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label" htmlFor="employee_name">
                Full Legal Name <span className="required">*</span>
              </label>
              <input
                id="employee_name"
                name="employee_name"
                type="text"
                required
                className="form-input"
                placeholder="e.g. Eleanor Vance"
                value={formData.employee_name}
                onChange={handleInputChange}
                disabled={isLoading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="email">
                Corporate Email <span className="required">*</span>
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                className="form-input"
                placeholder="e.vance@techcorp.io"
                value={formData.email}
                onChange={handleInputChange}
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label" htmlFor="phone">
                Phone Number <span className="required">*</span>
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                required
                className="form-input"
                placeholder="+1-555-010-9988"
                value={formData.phone}
                onChange={handleInputChange}
                disabled={isLoading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="joining_date">
                Joining Date <span className="required">*</span>
              </label>
              <input
                id="joining_date"
                name="joining_date"
                type="date"
                required
                className="form-input"
                value={formData.joining_date}
                onChange={handleInputChange}
                disabled={isLoading}
              />
            </div>
          </div>
        </div>

        {/* Section 2: Role Placement */}
        <div className="form-section">
          <div className="form-section-title">
            <span>2. Role Placement</span>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label" htmlFor="department">
                Department <span className="required">*</span>
              </label>
              <select
                id="department"
                name="department"
                className="form-select"
                value={formData.department}
                onChange={handleInputChange}
                disabled={isLoading}
              >
                <option value="Engineering">Engineering</option>
                <option value="Finance">Finance</option>
                <option value="Human Resources">Human Resources</option>
                <option value="Information Technology">Information Technology</option>
                <option value="Product & Design">Product & Design</option>
                <option value="Sales & Marketing">Sales & Marketing</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="designation">
                Designation / Job Title <span className="required">*</span>
              </label>
              <input
                id="designation"
                name="designation"
                type="text"
                required
                className="form-input"
                placeholder="e.g. Senior Backend Engineer"
                value={formData.designation}
                onChange={handleInputChange}
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group" style={{ gridColumn: "1 / -1" }}>
              <label className="form-label" htmlFor="manager">
                Reporting Manager <span className="required">*</span>
              </label>
              <input
                id="manager"
                name="manager"
                type="text"
                required
                className="form-input"
                placeholder="e.g. Marcus Vance (Director of Engineering)"
                value={formData.manager}
                onChange={handleInputChange}
                disabled={isLoading}
              />
            </div>
          </div>
        </div>

        {/* Section 3: Document Verification Checklist */}
        <div className="form-section">
          <div className="form-section-title">
            <span>3. Document Verification</span>
            <span className="form-section-subtext">
              Select verified or provided attachments
            </span>
          </div>

          <div className="doc-checklist-grid">
            <div
              className={`doc-toggle-card ${formData.documents.id_proof_submitted ? "checked" : ""}`}
              onClick={() => handleDocToggle("id_proof_submitted")}
              onKeyDown={(e) => handleKeyDown(e, "id_proof_submitted")}
              role="checkbox"
              aria-checked={formData.documents.id_proof_submitted}
              tabIndex={0}
            >
              <input
                type="checkbox"
                className="doc-checkbox"
                checked={formData.documents.id_proof_submitted}
                onChange={() => {}}
                tabIndex={-1}
                aria-hidden="true"
              />
              <div>
                <div className="doc-title">National ID / Passport</div>
                <div className="doc-desc">Government-issued identity verification</div>
              </div>
            </div>

            <div
              className={`doc-toggle-card ${formData.documents.address_proof_submitted ? "checked" : ""}`}
              onClick={() => handleDocToggle("address_proof_submitted")}
              onKeyDown={(e) => handleKeyDown(e, "address_proof_submitted")}
              role="checkbox"
              aria-checked={formData.documents.address_proof_submitted}
              tabIndex={0}
            >
              <input
                type="checkbox"
                className="doc-checkbox"
                checked={formData.documents.address_proof_submitted}
                onChange={() => {}}
                tabIndex={-1}
                aria-hidden="true"
              />
              <div>
                <div className="doc-title">Proof of Address</div>
                <div className="doc-desc">Utility bill or residential agreement</div>
              </div>
            </div>

            <div
              className={`doc-toggle-card ${formData.documents.bank_details_submitted ? "checked" : ""}`}
              onClick={() => handleDocToggle("bank_details_submitted")}
              onKeyDown={(e) => handleKeyDown(e, "bank_details_submitted")}
              role="checkbox"
              aria-checked={formData.documents.bank_details_submitted}
              tabIndex={0}
            >
              <input
                type="checkbox"
                className="doc-checkbox"
                checked={formData.documents.bank_details_submitted}
                onChange={() => {}}
                tabIndex={-1}
                aria-hidden="true"
              />
              <div>
                <div className="doc-title">Bank Account Details</div>
                <div className="doc-desc">Routing & account number for payroll</div>
              </div>
            </div>

            <div
              className={`doc-toggle-card ${formData.documents.education_certs_submitted ? "checked" : ""}`}
              onClick={() => handleDocToggle("education_certs_submitted")}
              onKeyDown={(e) => handleKeyDown(e, "education_certs_submitted")}
              role="checkbox"
              aria-checked={formData.documents.education_certs_submitted}
              tabIndex={0}
            >
              <input
                type="checkbox"
                className="doc-checkbox"
                checked={formData.documents.education_certs_submitted}
                onChange={() => {}}
                tabIndex={-1}
                aria-hidden="true"
              />
              <div>
                <div className="doc-title">Education Certificates</div>
                <div className="doc-desc">Degree transcripts and credential verification</div>
              </div>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "flex-end" }}>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isLoading}
            style={{ minWidth: "180px" }}
          >
            {isLoading ? (
              <>
                <span className="spinner" aria-hidden="true" />
                <span>Initiating Pipeline...</span>
              </>
            ) : (
              "Submit Onboarding"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
