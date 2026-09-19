// src/App.jsx — Root Application component with client-side routing & shared layout
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/Dashboard";
import WorkflowDetail from "./pages/WorkflowDetail";
import WorkflowHistory from "./pages/WorkflowHistory";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app-wrapper">
        <Navbar />

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
            Hierarchical Agent Coordination Framework &copy; {new Date().getFullYear()} • Powered by FastAPI &amp; Google Gemini AI
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
