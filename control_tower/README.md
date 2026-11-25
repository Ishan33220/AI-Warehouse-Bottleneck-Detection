# Warehouse Operations Control Tower (Agentic AI)

An Agentic AI upgrade to **AI-Assisted Warehouse Bottleneck Detection and Operational Efficiency Analysis**.  
All existing project files (`warehouse_orders.csv`, `kpi_summary.json`, `WarehouseDashboard.pbip`, notebooks, and analysis scripts) are preserved untouched.

> **Synthetic Data Notice:** All operational calculations and AI narratives run on the project's synthetic 2,000-order warehouse dataset (`warehouse_orders.csv`).

---

## Architecture

```
User / n8n Workflow
       │
       ▼
FastAPI Web Interface (web/app.py + Chat UI)
       │
       ▼
Orchestrator (agents/orchestrator.py)
       ├── 1. Warehouse Data Analysis Agent
       ├── 2. Order Delay Investigation Agent
       ├── 3. Bottleneck Detection Agent
       ├── 4. Shift Performance Analysis Agent
       ├── 5. Inventory Shortage Analysis Agent
       ├── 6. Operational Recommendation Agent (Human Approval Gate)
       └── 7. Automated Reporting Agent (Markdown + JSON + n8n)
       │
       ▼
Deterministic Python Tool Layer (tools/*.py) ──► warehouse_orders.csv
       │
       ▼
Gemini API Reasoning Layer (optional; offline fallback when key unset)
```

### Provenance Labels
Every response separates deterministic facts from AI reasoning and human decisions:
- 🟢 **`[COMPUTED]`** — Calculated directly from `warehouse_orders.csv` using Python/pandas.
- 🔵 **`[AI ANALYSIS]`** — Gemini-generated operational explanation grounded in the computed numbers (falls back to a deterministic summary when `GEMINI_API_KEY` is not configured).
- 🟡 **`[REQUIRES APPROVAL]`** — Consequential operational recommendations requiring explicit human approval (`POST /api/approve` → logged to `logs/approvals.jsonl`).

---

## Setup & Running

### 1. Install Dependencies
```powershell
cd control_tower
pip install -r requirements.txt
pip install fastapi uvicorn python-multipart httpx google-genai
```

### 2. Configure Environment Variables (Optional for Gemini)
Copy `.env.example` to `.env` and add your Google Gemini API key from [Google AI Studio](https://aistudio.google.com/):
```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash
```
*(Never commit `.env` to GitHub — it is listed in `.gitignore`.)*  
If `GEMINI_API_KEY` is omitted, all 7 agents and the web UI still run using offline fallback narratives.

### 3. Run the Control Tower Web Server
```powershell
cd control_tower
python -m uvicorn web.app:app --reload --port 8000
```
Open `http://localhost:8000` in your browser.

---

## The 7 Specialist Agents & Example Queries

| # | Agent | Example Query |
|---|-------|---------------|
| 1 | **Warehouse Data Analysis** | `"Show me the KPI overview"` |
| 2 | **Order Delay Investigation** | `"Why was ORD-100042 delayed?"` |
| 3 | **Bottleneck Detection** | `"What is the warehouse bottleneck?"` |
| 4 | **Shift Performance** | `"Which shift is busiest and how is workload balanced?"` |
| 5 | **Inventory Shortage** | `"What are the inventory shortage rates?"` |
| 6 | **Operational Recommendation** | `"What are your recommendations to improve operations?"` |
| 7 | **Automated Reporting** | `"Generate daily operations report"` |

---

## n8n Workflow Automation

Ready-to-import n8n workflows are located in `control_tower/n8n/`:
1. **`daily_report_workflow.json`** — Scheduled trigger (`0 7 * * *`) that calls `POST http://localhost:8000/api/chat` with the Reporting Agent and extracts the Markdown report path & summary.
2. **`alert_workflow.json`** — Webhook trigger (`POST /webhook/warehouse-delay-check`) that polls `GET http://localhost:8000/api/status`, checks if `on_time_delivery_pct < 85`, and invokes the Recommendation Agent when breached.

To use them:
1. Start the Control Tower server on port `8000`.
2. In n8n, choose **Import from File** and select either JSON file.

---

## Running Tests

```powershell
cd control_tower
python -m pytest tests/ -v
```
