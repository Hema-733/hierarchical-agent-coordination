# 🤖 Hierarchical Multi-Agent Onboarding Coordination System

An intelligent, multi-agent automated employee onboarding orchestration system built with **FastAPI**, **Google Gemini**, **MongoDB**, and **React + Vite**.

---

## 🏗️ Architecture Overview

The system uses a **Hierarchical Multi-Agent** architecture:

```
                  ┌────────────────────────┐
                  │ Master Coordinator      │
                  │ Agent (Gemini Powered) │
                  └───────────┬────────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
     ┌───────────────┐┌───────────────┐┌───────────────┐
     │  IT Provision ││  HR Document  ││   Training    │
     │  Worker Agent ││  Worker Agent ││Scheduler Agent│
     └───────────────┘└───────────────┘└───────────────┘
```

1. **Master Coordinator Agent (`app/agents/coordinator.py`)**:
   - Parses employee onboarding profiles.
   - Decomposes the onboarding goal into subtasks with dependencies.
   - Evaluates worker outputs and updates workflow status dynamically.
2. **Worker Agents (`app/agents/worker_agents.py`)**:
   - **IT Provisioning Agent**: Allocates email, Slack, GitHub, laptop specifications, and access permissions based on role and department.
   - **HR Document Agent**: Generates compliance checklists, NDA/contracts, tax documents, and employee handbook assignments.
   - **Training Scheduler Agent**: Schedules orientation sessions, mentor pairings, role-based curriculums, and week 1 check-ins.
3. **Database Repository (`app/db/repositories/workflow_repo.py`)**:
   - Persists onboarding requests, generated task plans, execution logs, and live agent activity streams in MongoDB.
4. **React Frontend (`frontend/`)**:
   - Interactive onboarding initiation form.
   - Live Dashboard displaying active workflows, completion metrics, and status cards.
   - Detailed workflow view with real-time logs, dependency status, and agent action insights.

---

## 🚀 Quick Setup & Run Guide

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & `npm`
- **MongoDB** running locally on port `27017` (or MongoDB Atlas connection string)
- **Google Gemini API Key** (from Google AI Studio)

---

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env from template
copy .env.example .env   # On Windows
# cp .env.example .env   # On Linux/macOS
```

> **Important:** Edit `backend/.env` to configure your `GEMINI_API_KEY` and `MONGODB_URI`:
> ```env
> MONGODB_URI=mongodb://localhost:27017
> MONGODB_DB_NAME=onboarding_db
> GEMINI_API_KEY=your_actual_gemini_api_key
> APP_HOST=0.0.0.0
> APP_PORT=8001
> DEBUG=true
> FRONTEND_ORIGIN=http://localhost:5173
> ```

**Start the Backend Server:**
```bash
python run.py
# Backend runs at http://localhost:8001
# Interactive Swagger docs at http://localhost:8001/docs
```

---

### 3. Frontend Setup

Open a separate terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env from template
copy .env.example .env   # On Windows
# cp .env.example .env   # On Linux/macOS
```

Ensure `frontend/.env` has:
```env
VITE_API_BASE_URL=http://localhost:8001
```

**Start the Frontend Dev Server:**
```bash
npm run dev
# Frontend runs at http://localhost:5173
```

---

## 🧪 Testing Backend End-to-End

To verify MongoDB connection, Gemini API key, and full agent execution:
```bash
cd backend
python test_e2e.py
```

---

## 📁 Repository Structure

```
hierarchical-agent-coordination/
├── backend/
│   ├── app/
│   │   ├── agents/          # Coordinator & Worker agents
│   │   ├── api/             # FastAPI route handlers
│   │   ├── db/              # MongoDB client & repositories
│   │   ├── models/          # Pydantic data schemas
│   │   └── services/        # Orchestration & business logic
│   ├── .env.example
│   ├── requirements.txt
│   ├── run.py               # Uvicorn entry point (Port 8001)
│   └── test_e2e.py          # End-to-end verification script
├── frontend/
│   ├── src/
│   │   ├── api/             # Axios API client
│   │   ├── components/      # UI components (Navbar, Logs, Badges, etc.)
│   │   ├── pages/           # Dashboard, Onboarding, WorkflowDetail, History
│   │   └── App.jsx
│   ├── .env.example
│   ├── package.json
│   └── vite.config.js
├── notes/
│   └── images/              # Directory for screenshots & design mockups
├── NOTES_AND_CHANGES.md     # Scratchpad for notes, images, & pending changes
└── README.md
```
