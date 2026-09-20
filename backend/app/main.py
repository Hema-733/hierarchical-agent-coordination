"""
main.py — FastAPI application entry point.

Initializes:
- Lifespan management (MongoDB connection + Agent seed initialization)
- CORS Middleware for React frontend
- Routers for Onboarding, Workflows, Tasks, and Agents
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.connection import connect_to_mongo, close_mongo_connection
from app.db.seed import seed_agents

# Feature Routers
from app.api.onboarding import router as onboarding_router
from app.api.workflows import router as workflows_router
from app.api.tasks import router as tasks_router
from app.api.agents import router as agents_router


from app.agents.supervisor_agent import supervisor_agent
from app.agents.hr_agent import hr_agent
from app.agents.it_agent import it_agent
from app.agents.finance_agent import finance_agent
from app.agents.resource_agent import resource_agent

# ---------------------------------------------------------------------------
# Lifespan: startup + shutdown logic
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Code before `yield` runs at startup.
    Code after `yield` runs at shutdown.
    """
    print("[App] Starting up...")
    await connect_to_mongo()
    await seed_agents()
    
    # Register all specialized sub-agents with the Supervisor
    supervisor_agent.register_sub_agent(hr_agent)
    supervisor_agent.register_sub_agent(it_agent)
    supervisor_agent.register_sub_agent(finance_agent)
    supervisor_agent.register_sub_agent(resource_agent)
    
    yield
    print("[App] Shutting down...")
    await close_mongo_connection()


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Hierarchical Agent Coordination Framework",
    description="Employee Onboarding powered by a Supervisor + Specialized Agents",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS — allow the React frontend to call this API
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_ORIGIN,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Simple health check.
    Returns 200 if the server is running.
    """
    return {
        "status": "ok",
        "app": "Hierarchical Agent Coordination Framework",
        "version": "1.0.0",
    }


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(onboarding_router, prefix="/onboarding", tags=["Onboarding"])
app.include_router(workflows_router, prefix="/workflow", tags=["Workflows"])
app.include_router(tasks_router, prefix="/task", tags=["Tasks"])
app.include_router(agents_router, prefix="/agent", tags=["Agents"])
