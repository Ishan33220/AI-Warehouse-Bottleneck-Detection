"""
FastAPI Web Interface for the Warehouse Operations Control Tower.

Exposes:
  GET  /            -> Chat UI (index.html)
  POST /api/chat    -> Route natural-language query to specialist agent
  POST /api/approve -> Record human approval/rejection of flagged recommendation
  GET  /api/status  -> Dataset health, row count, Gemini status
  GET  /api/agents  -> List of the 7 specialist agents
"""

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from agents.orchestrator import Orchestrator
from config.settings import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LOGS_DIR,
    OUTPUTS_DIR,
    PROJECT_ROOT,
)
from tools.kpi_calculator import compute_core_kpis

logger = logging.getLogger(__name__)

WEB_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

# Ensure runtime directories exist
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Shared orchestrator instance (lazily loads dataset on first request or startup)
orchestrator = Orchestrator()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Pre-load dataset so first query is fast."""
    try:
        orchestrator.load_data()
    except Exception as exc:
        logger.warning("Startup dataset load failed: %s", exc)
    yield


app = FastAPI(
    title="Warehouse Operations Control Tower",
    description="Agentic AI Control Tower built on warehouse_orders.csv",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ── Request Models ───────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    agent: Optional[str] = None  # Optional explicit agent key


class ApprovalRequest(BaseModel):
    approval_item: str
    decision: str  # "approved" or "rejected"
    agent: Optional[str] = None
    notes: Optional[str] = ""


# ── Endpoints ────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the Control Tower chat interface."""
    return templates.TemplateResponse(request, "index.html")


@app.post("/api/chat")
async def chat(payload: ChatRequest):
    """
    Dispatch a user query to the appropriate specialist agent.
    If `agent` is explicitly provided and valid, route directly to that agent.
    """
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if payload.agent and payload.agent in orchestrator._agents:
        agent_obj = orchestrator._agents[payload.agent]
        params = orchestrator._extract_params(query, payload.agent)
        response = agent_obj.run(query, orchestrator.df, **params)
    else:
        response = orchestrator.dispatch(query)

    data = response.to_dict()
    # Convert local chart file paths to /outputs/<filename> URLs for the browser
    data["chart_urls"] = [f"/outputs/{Path(p).name}" for p in data.get("charts", [])]
    data["gemini_active"] = bool(GEMINI_API_KEY)
    return data


@app.post("/api/approve")
async def approve(payload: ApprovalRequest):
    """
    Log a human-in-the-loop approval or rejection decision to logs/approvals.jsonl.
    """
    decision = payload.decision.lower().strip()
    if decision not in {"approved", "rejected"}:
        raise HTTPException(
            status_code=400,
            detail="Decision must be 'approved' or 'rejected'.",
        )

    record = {
        "timestamp": datetime.now().isoformat(),
        "decision": decision,
        "approval_item": payload.approval_item,
        "agent": payload.agent or "Operational Recommendation Agent",
        "notes": payload.notes or "",
    }

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / "approvals.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return {"status": "recorded", "record": record}


@app.get("/api/status")
async def status():
    """Return dataset health, summary metrics, and AI configuration status."""
    df = orchestrator.df
    kpis = compute_core_kpis(df)
    pbip_exists = (PROJECT_ROOT / "WarehouseDashboard.pbip").exists()
    return {
        "status": "online",
        "dataset": {
            "rows": len(df),
            "columns": len(df.columns),
            "date_min": str(df["Order_Date"].min())[:10],
            "date_max": str(df["Order_Date"].max())[:10],
            "on_time_delivery_pct": kpis.get("on_time_delivery_pct"),
            "delayed_orders": kpis.get("delayed_orders"),
            "synthetic_notice": "Synthetic warehouse order dataset (2,000 orders)",
        },
        "ai": {
            "gemini_configured": bool(GEMINI_API_KEY),
            "model": GEMINI_MODEL,
            "mode": "live" if GEMINI_API_KEY else "offline_fallback",
        },
        "power_bi": {
            "preserved": pbip_exists,
            "file": "WarehouseDashboard.pbip",
        },
    }


@app.get("/api/agents")
async def list_agents():
    """Return the 7 specialist agents and their descriptions."""
    return {"agents": orchestrator.available_agents()}
