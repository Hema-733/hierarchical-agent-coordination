// src/components/Navbar.jsx — Main responsive top navigation bar with backend status ping
import { useState, useEffect } from "react";
import { NavLink, Link } from "react-router-dom";
import { checkBackendHealth } from "../api/client";

export default function Navbar() {
  const [isBackendHealthy, setIsBackendHealthy] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const verifyHealth = async () => {
      try {
        const res = await checkBackendHealth();
        if (isMounted) {
          setIsBackendHealthy(res && res.status === "ok");
        }
      } catch {
        if (isMounted) {
          setIsBackendHealthy(false);
        }
      }
    };

    verifyHealth();
    const interval = setInterval(verifyHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="app-header">
      <div className="navbar-container">
        {/* Brand Identity */}
        <Link to="/" className="brand-section">
          <div className="brand-icon-wrapper">
            <svg
              className="brand-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
          </div>
          <div className="brand-text">
            <span className="brand-title">AgentFlow</span>
            <span className="brand-subtitle">Hierarchical Coordination</span>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav>
          <ul className="nav-links">
            <li>
              <NavLink
                to="/onboarding"
                className={({ isActive }) =>
                  `nav-link ${isActive ? "active" : ""}`
                }
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                  <circle cx="8.5" cy="7" r="4" />
                  <line x1="20" y1="8" x2="20" y2="14" />
                  <line x1="23" y1="11" x2="17" y2="11" />
                </svg>
                <span>New Onboarding</span>
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `nav-link ${isActive ? "active" : ""}`
                }
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="3" y="3" width="7" height="7" />
                  <rect x="14" y="3" width="7" height="7" />
                  <rect x="14" y="14" width="7" height="7" />
                  <rect x="3" y="14" width="7" height="7" />
                </svg>
                <span>Dashboard</span>
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/history"
                className={({ isActive }) =>
                  `nav-link ${isActive ? "active" : ""}`
                }
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                <span>History</span>
              </NavLink>
            </li>
          </ul>
        </nav>

        {/* Backend Connectivity Status Badge */}
        <div className="nav-status">
          <div className="health-badge" title="FastAPI Backend Health Status">
            {isBackendHealthy === null ? (
              <>
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: "#94a3b8",
                  }}
                />
                <span>Checking API...</span>
              </>
            ) : isBackendHealthy ? (
              <>
                <span className="pulse-active" />
                <span style={{ color: "#34d399" }}>API Online</span>
              </>
            ) : (
              <>
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: "#f59e0b",
                  }}
                />
                <span style={{ color: "#fbbf24" }}>API Standby</span>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
