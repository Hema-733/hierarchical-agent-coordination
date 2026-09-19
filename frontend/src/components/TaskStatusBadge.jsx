// src/components/TaskStatusBadge.jsx — Visual color-coded badge for workflow & task execution states

export default function TaskStatusBadge({ status, size = "md", showIcon = true }) {
  const normStatus = (status || "PENDING").toUpperCase();

  let badgeClass = "badge-primary";
  let icon = null;

  switch (normStatus) {
    case "COMPLETED":
      badgeClass = "badge-success";
      icon = (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      );
      break;

    case "RUNNING":
      badgeClass = "badge-primary";
      icon = <span className="pulse-active" style={{ width: 6, height: 6 }} />;
      break;

    case "READY":
      badgeClass = "badge-primary";
      icon = (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <polygon points="5 3 19 12 5 21 5 3" />
        </svg>
      );
      break;

    case "PAUSED":
      badgeClass = "badge-warning";
      icon = (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
          <rect x="6" y="4" width="4" height="16" />
          <rect x="14" y="4" width="4" height="16" />
        </svg>
      );
      break;

    case "FAILED":
      badgeClass = "badge-danger";
      icon = (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      );
      break;

    case "BLOCKED":
      badgeClass = "badge-warning";
      icon = (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <circle cx="12" cy="12" r="10" />
          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
        </svg>
      );
      break;

    case "PENDING":
    default:
      badgeClass = "badge-secondary";
      icon = (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
      );
      break;
  }

  const isSmall = size === "sm";

  return (
    <span
      className={`badge ${badgeClass}`}
      style={{
        fontSize: isSmall ? "0.7rem" : "0.775rem",
        padding: isSmall ? "2px 8px" : "4px 10px",
      }}
    >
      {showIcon && icon}
      <span>{normStatus}</span>
    </span>
  );
}
