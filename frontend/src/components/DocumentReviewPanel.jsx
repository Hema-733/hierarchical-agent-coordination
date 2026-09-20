// src/components/DocumentReviewPanel.jsx — Human-in-the-Loop Document Verification Panel
import { useState } from "react";

const DOC_SPECS = [
  {
    key: "id_proof",
    title: "National ID / Passport",
    requiredBy: "Document Verification (HR Agent)",
    defaultFilename: "national_id.pdf",
    description: "Government-issued passport or national ID card confirming identity.",
  },
  {
    key: "address_proof",
    title: "Proof of Address",
    requiredBy: "Document Verification (HR Agent)",
    defaultFilename: "utility_bill.pdf",
    description: "Recent utility bill, lease agreement, or official residency certificate.",
  },
  {
    key: "bank_details",
    title: "Bank Account Details",
    requiredBy: "Payroll Setup (Finance Agent)",
    defaultFilename: "bank_account_mandate.pdf",
    description: "Official bank mandate or voided cheque for direct salary deposits.",
  },
  {
    key: "education_certs",
    title: "Education Certificates",
    requiredBy: "HR Verification (HR Agent)",
    defaultFilename: "degree_certificate.pdf",
    description: "Certified degree diplomas and relevant academic qualifications.",
  },
];

function getStatusBadgeClass(status) {
  switch (status) {
    case "VERIFIED":
      return "badge-success";
    case "UNDER_REVIEW":
      return "badge-primary";
    case "SUBMITTED":
      return "badge-warning";
    case "REJECTED":
      return "badge-danger";
    case "MISSING":
    default:
      return "badge-neutral";
  }
}

export default function DocumentReviewPanel({
  employee,
  workflow,
  onUpdateDocument,
  actionLoading,
}) {
  const [rejectingKey, setRejectingKey] = useState(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [docNameInput, setDocNameInput] = useState({});

  if (!employee) {
    return (
      <div className="card doc-review-panel" style={{ padding: "2rem", textAlign: "center" }}>
        <p className="text-muted">Loading candidate document verification records...</p>
      </div>
    );
  }

  const docs = employee.documents || {};

  const handleVerify = (docKey, autoResume = true) => {
    onUpdateDocument(
      docKey,
      {
        status: "VERIFIED",
        submitted: true,
        verified_by: "HR Operator",
        review_note: "Verified via HR Management Console",
      },
      autoResume
    );
  };

  const handleMarkSubmitted = (docKey, defaultName) => {
    const filename = docNameInput[docKey]?.trim() || defaultName;
    onUpdateDocument(
      docKey,
      {
        status: "SUBMITTED",
        submitted: true,
        document_name: filename,
        review_note: "Document submitted for review",
      },
      false
    );
    setDocNameInput((prev) => ({ ...prev, [docKey]: "" }));
  };

  const handleUnderReview = (docKey) => {
    onUpdateDocument(
      docKey,
      {
        status: "UNDER_REVIEW",
        submitted: true,
        review_note: "Under manual verification by HR",
      },
      false
    );
  };

  const handleConfirmReject = (docKey) => {
    const reason = rejectionReason.trim() || "Document rejected by HR operator.";
    onUpdateDocument(
      docKey,
      {
        status: "REJECTED",
        submitted: false,
        review_note: reason,
      },
      false
    );
    setRejectingKey(null);
    setRejectionReason("");
  };

  return (
    <div className="doc-review-panel card">
      <div className="doc-review-header">
        <div>
          <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 600 }}>
            Human-in-the-Loop Document Verification
          </h3>
          <p style={{ margin: "4px 0 0", fontSize: "0.825rem", color: "var(--text-muted)" }}>
            Review, verify, or reject employee compliance records. Verifying required documents unblocks paused workflow tasks.
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span className="badge badge-neutral">Candidate: {employee.employee_id}</span>
        </div>
      </div>

      <div className="doc-review-grid">
        {DOC_SPECS.map((spec) => {
          const docData = docs[spec.key] || {};
          const status = docData.status || (docData.submitted ? "SUBMITTED" : "MISSING");
          const isVerified = status === "VERIFIED";
          const isMissing = status === "MISSING";
          const isRejected = status === "REJECTED";
          const isRejectingThis = rejectingKey === spec.key;

          return (
            <div
              key={spec.key}
              className={`doc-review-card ${isRejected ? "doc-card-rejected" : isVerified ? "doc-card-verified" : ""}`}
            >
              <div className="doc-card-top">
                <div>
                  <div className="doc-card-title">{spec.title}</div>
                  <div className="doc-card-sub">{spec.requiredBy}</div>
                </div>
                <span className={`badge ${getStatusBadgeClass(status)}`}>
                  {status}
                </span>
              </div>

              <div className="doc-card-meta">
                <div className="doc-meta-row">
                  <span className="doc-meta-label">File Record:</span>
                  <span className="doc-meta-value font-mono">
                    {docData.document_name || spec.defaultFilename}
                  </span>
                </div>
                <div className="doc-meta-row">
                  <span className="doc-meta-label">Intake Status:</span>
                  <span className="doc-meta-value">
                    {docData.submitted ? "Submitted" : "Not Submitted"}
                  </span>
                </div>
                {docData.verified_by && (
                  <div className="doc-meta-row">
                    <span className="doc-meta-label">Verified By:</span>
                    <span className="doc-meta-value">{docData.verified_by}</span>
                  </div>
                )}
                {docData.review_note && (
                  <div className="doc-meta-note">
                    <span className="doc-meta-label">Note / Reason:</span>
                    <p style={{ margin: "2px 0 0", color: isRejected ? "var(--status-danger)" : "var(--text-secondary)", fontSize: "0.8rem" }}>
                      {docData.review_note}
                    </p>
                  </div>
                )}
              </div>

              {/* Inline rejection prompt */}
              {isRejectingThis && (
                <div className="doc-inline-reject-box">
                  <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--status-danger)" }}>
                    Rejection Reason:
                  </label>
                  <input
                    type="text"
                    className="form-input form-input-sm"
                    placeholder="e.g. Blurry photo, mismatch in name"
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    disabled={actionLoading}
                    autoFocus
                  />
                  <div style={{ display: "flex", gap: "6px", marginTop: "6px" }}>
                    <button
                      type="button"
                      className="btn btn-sm btn-danger"
                      onClick={() => handleConfirmReject(spec.key)}
                      disabled={actionLoading}
                    >
                      Confirm Reject
                    </button>
                    <button
                      type="button"
                      className="btn btn-sm btn-secondary"
                      onClick={() => {
                        setRejectingKey(null);
                        setRejectionReason("");
                      }}
                      disabled={actionLoading}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              {!isRejectingThis && (
                <div className="doc-card-actions">
                  {isVerified ? (
                    <div style={{ display: "flex", gap: "6px", width: "100%" }}>
                      <span className="text-muted" style={{ fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "4px" }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--status-success)" strokeWidth="2.5">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                        Compliance check passed
                      </span>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        style={{ marginLeft: "auto", fontSize: "0.75rem" }}
                        onClick={() => setRejectingKey(spec.key)}
                        disabled={actionLoading}
                      >
                        Revoke
                      </button>
                    </div>
                  ) : (
                    <>
                      <button
                        type="button"
                        className="btn btn-primary btn-sm doc-btn-verify"
                        onClick={() => handleVerify(spec.key, true)}
                        disabled={actionLoading}
                        title="Verify document and resume workflow if paused"
                      >
                        Verify & Resume
                      </button>

                      {status !== "UNDER_REVIEW" && (
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleUnderReview(spec.key)}
                          disabled={actionLoading}
                          title="Flag document as under active review"
                        >
                          Under Review
                        </button>
                      )}

                      {isMissing && (
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleMarkSubmitted(spec.key, spec.defaultFilename)}
                          disabled={actionLoading}
                          title="Simulate document upload / intake"
                        >
                          Mark Submitted
                        </button>
                      )}

                      <button
                        type="button"
                        className="btn btn-secondary btn-sm doc-btn-reject"
                        onClick={() => {
                          setRejectingKey(spec.key);
                          setRejectionReason("");
                        }}
                        disabled={actionLoading}
                        title="Reject document with feedback"
                      >
                        Reject
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
