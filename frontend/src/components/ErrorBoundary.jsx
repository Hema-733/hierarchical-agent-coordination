// src/components/ErrorBoundary.jsx — Enterprise-grade React error boundary
import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log to console for diagnostic monitoring; do not expose stack trace to user UI
    console.error("ErrorBoundary caught an unexpected render error:", error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "var(--bg-secondary)",
            padding: "2rem",
            color: "var(--text-primary)",
          }}
        >
          <div
            style={{
              maxWidth: "480px",
              width: "100%",
              backgroundColor: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
              padding: "2rem",
              boxShadow: "var(--shadow-md)",
              textAlign: "center",
            }}
          >
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "50%",
                backgroundColor: "var(--status-danger-bg, #fef2f2)",
                color: "var(--status-danger, #991b1b)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 1.25rem",
              }}
            >
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <h2
              style={{
                fontSize: "1.25rem",
                fontWeight: 600,
                color: "var(--text-primary)",
                marginBottom: "0.5rem",
              }}
            >
              Application Error
            </h2>
            <p
              style={{
                fontSize: "0.875rem",
                color: "var(--text-muted)",
                lineHeight: "1.5",
                marginBottom: "1.5rem",
              }}
            >
              The application encountered an unexpected runtime error while rendering this view.
              Please reload the application to restore operations.
            </p>
            <button
              type="button"
              className="btn btn-primary"
              onClick={this.handleReload}
              style={{ width: "100%" }}
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
