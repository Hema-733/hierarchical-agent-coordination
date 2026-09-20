// src/App.jsx — Root Application component with client-side routing & shared layout
import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import ErrorBoundary from "./components/ErrorBoundary";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/Dashboard";
import WorkflowDetail from "./pages/WorkflowDetail";
import WorkflowHistory from "./pages/WorkflowHistory";
import "./App.css";

function getInitialTheme() {
  const saved = localStorage.getItem("theme");
  if (saved === "light" || saved === "dark") {
    return saved;
  }
  if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "light";
}

function App() {
  const [theme, setTheme] = useState(getInitialTheme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  return (
    <BrowserRouter>
      <ErrorBoundary>
        <div className="app-wrapper">
          <Navbar theme={theme} onToggleTheme={toggleTheme} />

          <main className="main-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/onboarding" element={<Onboarding />} />
              <Route path="/workflows/:id" element={<WorkflowDetail />} />
              <Route path="/history" element={<WorkflowHistory />} />
              {/* Fallback to onboarding */}
              <Route path="*" element={<Navigate to="/onboarding" replace />} />
            </Routes>
          </main>

          <footer className="app-footer">
            <div>
              Hierarchical Agent Coordination Framework &copy; {new Date().getFullYear()} • Enterprise Onboarding Platform
            </div>
          </footer>
        </div>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
