# Viva Preparation Guide
## Agentic Warehouse Operations Assistant – Warehouse Operations Control Tower

**Project Team (MBA – Operations & Business Analytics):** Ishan Mishra, Remee, Nishu, Taniya  
**Dataset:** `warehouse_orders.csv` (2,000 synthetic orders, Sept–Oct 2026)

---

## Part A: Beginner-Friendly Explanations (Agentic AI & Control Tower)

### 1. What is an AI agent?
An AI agent is a specialized software component that can **observe a question or situation, use tools (such as Python scripts or databases) to gather real facts, reason about what those facts mean, and produce a structured output or action**. Unlike a basic chatbot that only guesses answers from memory, an AI agent uses real tools before speaking.

### 2. What makes this application "agentic"?
Our Control Tower is *agentic* because it does not just return a single static chart or a generic text reply. Instead:
1. It **routes** each user question to the right specialist agent (out of 7 agents).
2. Each agent **calls deterministic Python tools** to query and calculate numbers from `warehouse_orders.csv` (and the Recommendation Agent even **calls 3 other agents**—Bottleneck, Shift, and Inventory—before synthesizing advice).
3. It separates **computed facts (`🟢 [COMPUTED]`)** from **AI reasoning (`🔵 [AI ANALYSIS]`)**.
4. It enforces a **human-in-the-loop approval gate (`🟡 [REQUIRES APPROVAL]`)** before any operational change is accepted.

### 3. What is the role of the Orchestrator?
The **Control Tower Orchestrator** (`control_tower/agents/orchestrator.py`) acts like a **warehouse shift manager at the front desk**. When a user types a question (e.g., *"Why was ORD-100042 delayed?"* or *"Which shift is busiest?"*), the Orchestrator:
- Classifies the intent using keyword/pattern matching.
- Extracts parameters such as `Order_ID`, `Shift` (`Morning`/`Evening`/`Night`), `Zone` (`Metro`/`Tier-2`/`Remote`), or date filters.
- Dispatches the request to the right specialist agent (or lets the user pick an agent directly in the UI sidebar).

### 4. How does Python calculate warehouse KPIs?
Python (`pandas` and `numpy`) reads `warehouse_orders.csv` (2,000 rows, 24 columns) via `tools/data_loader.py` and runs verified formulas in `tools/kpi_calculator.py`, `bottleneck_detector.py`, `shift_analyzer.py`, `inventory_analyzer.py`, `cost_analyzer.py`, and `order_investigator.py`.  
For example:
- **On-Time Delivery %** = `On-Time Orders / (On-Time + Delayed Orders)` = **83.1%** (excluding cancelled and in-transit orders).
- **Packing Bottleneck** = **123 delays out of 328 total delayed orders (37.5%)**.
- Every KPI is cross-checked against `kpi_summary.json` and covered by automated `pytest` unit tests.

### 5. What is FastAPI?
**FastAPI** is a modern, lightweight Python web framework used to expose our Python agents as a web application (`control_tower/web/app.py`) running at `http://localhost:8000`. It serves the interactive HTML/CSS/JS chat interface (`GET /`) and provides JSON APIs (`POST /api/chat`, `POST /api/approve`, `GET /api/status`, `GET /api/agents`).

### 6. What is n8n and how will it automate reporting?
**n8n** is a low-code workflow automation tool (similar to Zapier, but self-hostable). We created two n8n workflow JSON files in `control_tower/n8n/`:
- `daily_report_workflow.json`: Scheduled for 07:00 daily to call `POST http://localhost:8000/api/chat` and generate the Markdown report and KPI snapshot.
- `alert_workflow.json`: Webhook-triggered workflow that checks `GET /api/status` and triggers recommendations if on-time delivery falls below 85%.  
*(Honest status: The JSON workflows are created and syntax-validated, but live execution inside a running n8n server has not yet been demonstrated.)*

### 7. What is Generative AI's role?
Generative AI (designed for **Google Gemini** via `google-genai`) is **not** used to do math or invent KPIs. Its role is strictly to **interpret the Python-computed numbers in plain business English**—explaining *why* Packing is congested, *what* Evening shift imbalance means for managers, and *how* to prioritize actions.  
*(Honest status: The Gemini API key is not connected yet, so the live UI currently runs in **Offline Fallback** mode using deterministic narrative templates.)*

### 8. Why is human approval necessary?
In real warehouse operations, changing shift rosters, adding temporary packing staff, or increasing safety stock costs money and affects employees. An AI system should **recommend**, not silently execute, consequential business decisions. Our **Human Approval Gate (`🟡 [REQUIRES APPROVAL]`)** requires a manager to click **Approve Action** or **Reject**, logging the decision and timestamp to `control_tower/logs/approvals.jsonl` for auditability.

### 9. What is the difference between rule-based automation and Generative AI?
- **Rule-based automation (Python tools + DAX):** Follows exact, fixed formulas (e.g., `if Total_Time_Minutes > SLA_Minutes: Delayed`). It gives the **exact same number** every time and never hallucinates, but it cannot write tailored management explanations.
- **Generative AI (Gemini):** Reads those verified numbers and generates flexible, human-readable summaries, root-cause narratives, and prioritized recommendations. Combining both gives **accuracy + readability**.

### 10. What did Antigravity help develop?
**Google Antigravity** (AI coding assistant) was used as the development environment to design the modular `control_tower/` architecture, implement the 7 specialist agents and Python tool wrappers, build the FastAPI web UI, create the n8n workflow JSON templates, write **125 automated `pytest` tests** (all 125 passing in our development test run), and prepare the academic documentation—while preserving all original project files untouched.

### 11. What are the current limitations?
1. **Synthetic Data Only:** All 2,000 orders were generated via `generate_dataset.py` (with the Packing bottleneck deliberately embedded), so results prove the *methodology*, not a real warehouse.
2. **Gemini API Not Connected Yet:** Live LLM reasoning has not been demonstrated yet; the system currently uses offline fallback text.
3. **n8n Live Execution Pending:** The two n8n workflows are exported as JSON but have not yet been executed inside a live n8n instance.
4. **Keyword-Based Orchestrator Routing:** The Orchestrator currently routes queries using regex keyword rules rather than an LLM router, so very unusual phrasing may default to the Data Analysis Agent.
5. **No Live ERP/WMS Connection:** Reads a static CSV (`warehouse_orders.csv`) rather than a live warehouse database.

---

## Part B: Preserved Power BI & 4-Student Viva Script

*(Preserved from `dashboard_explained_and_viva_guide.md` so both the original Power BI dashboard and the new Control Tower are covered seamlessly.)*

### Power BI Pages Summary
| Page | Question It Answers |
|---|---|
| 1. Warehouse Overview | *"How is the warehouse doing overall?"* (2,000 orders, 1,941 delivered, 328 delayed, 83.1% on-time, ₹762,668 cost) |
| 2. Bottleneck Analysis | *"Which stage is causing the delays, and why?"* (Packing = 123 delays / 37.5%; 75.0% warehouse-controlled) |
| 3. Inventory & Workforce Efficiency | *"Do we have the stock and the people to cope?"* (8.2% OOS overall; Electronics 12.1%, Toys & Games 10.5%; Evening shift 139.6 orders/employee vs. Night 40.8) |

### 60–75 Second Viva Roles (4 Team Members)
- **Student 1 (Data & Business Research Analyst — Page 1 & Synthetic Data):** Explains the 2,000 synthetic orders (Sept–Oct 2026), why real company data is confidential, why cancelled/in-transit orders leave stage cells blank, and the festive surge (15–21 Oct).
- **Student 2 (Business Intelligence Analyst — KPIs & DAX):** Explains the 24 DAX measures, `DIVIDE()` safety against zero denominators, and why `On-Time % = 83.1%` excludes cancelled/in-transit orders.
- **Student 3 (Generative AI Developer — Page 2, Agents & Grounding):** Explains how Packing (123 delays, 37.5%) is computed in Python/Power BI first, and then passed to the 7-agent Control Tower so AI narratives only cite `[COMPUTED]` facts (currently via offline fallback until `GEMINI_API_KEY` is added).
- **Student 4 (Automation & Integration Analyst — Page 3, FastAPI, Human Approval & n8n):** Explains shift imbalance (Evening vs. Night), Electronics/Toys & Games stock-outs, the FastAPI UI at `localhost:8000`, the `🟡 [REQUIRES APPROVAL]` audit log, and how the n8n JSON workflows are designed to automate daily reports and SLA alerts.
