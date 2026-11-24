# Agentic Warehouse Operations Assistant – Warehouse Operations Control Tower

## Project Overview

An MBA academic project focused on identifying warehouse bottlenecks, analysing order delays, and improving operational efficiency through data analytics, Python automation, Power BI dashboards, and a multi-agent warehouse operations control tower.

The project was developed in two phases:

- **Phase 1 – Warehouse Analytics:** Synthetic data generation, data cleaning, exploratory analysis, rule-based bottleneck detection, and Power BI dashboard development.
- **Phase 2 – Agentic Control Tower:** A FastAPI-based application integrating seven specialist agents, deterministic Python analytical tools, operational recommendations, and a human-in-the-loop approval mechanism.

The project demonstrates how traditional warehouse analytics can be extended into an AI-assisted operational decision-support system.

**Important:** This is an academic project using synthetic warehouse data, not actual company records or live warehouse operations.

---

## Problem Statement

Warehouse operations involve multiple stages, including receiving, inventory checking, picking, packing, dispatch, and delivery.

Delays, inventory shortages, workload imbalances, and operational inefficiencies can negatively affect order fulfilment, delivery performance, and operational costs.

This project aims to analyse warehouse performance, identify major bottlenecks, investigate operational issues, and provide practical recommendations through an integrated analytics and decision-support system.

---

## Project Objectives

1. Analyse warehouse order and delivery performance.
2. Identify operational bottlenecks and delay patterns.
3. Evaluate warehouse shift performance and inventory risks.
4. Develop interactive Power BI dashboards.
5. Automate KPI calculations and operational analysis using Python.
6. Build a multi-agent Control Tower for investigating warehouse issues.
7. Introduce human approval before operational decisions are recorded.

---

## Tools and Technologies

| Technology | Purpose |
|---|---|
| Python | Data processing and analytical tools |
| Pandas | Data cleaning and manipulation |
| Jupyter Notebook | Data analysis and experimentation |
| Power BI | Interactive dashboards and KPI visualisation |
| Excel / CSV | Dataset management |
| FastAPI | Control Tower backend |
| Python Agents | Specialist operational analysis |
| Gemini API | Planned AI reasoning integration |
| n8n | Workflow automation blueprints |
| GitHub | Version control and documentation |
| Claude AI / Google Antigravity | Development assistance |

---

## Project Methodology

### Phase 1 – Foundational Warehouse Analytics

1. Generated a synthetic warehouse dataset containing 2,000 orders.
2. Cleaned and processed the dataset using Python and Pandas.
3. Performed exploratory data analysis.
4. Calculated warehouse performance KPIs.
5. Identified bottlenecks using predefined rule-based logic.
6. Developed interactive Power BI dashboards.
7. Validated analytical outputs through independent checks.

### Phase 2 – Agentic Warehouse Operations Control Tower

1. Developed a FastAPI-based Control Tower application.
2. Integrated seven specialist operational agents.
3. Connected agents with deterministic Python analytical tools.
4. Implemented automated order investigation and bottleneck analysis.
5. Added operational recommendations and output provenance labels.
6. Introduced human-in-the-loop approval and audit logging.
7. Prepared n8n workflow automation blueprints.

---

## Key Performance Indicators and Findings

| KPI | Result |
|---|---:|
| Total Orders | 2,000 |
| Delivered Orders | 1,941 |
| Cancelled Orders | 52 |
| Orders in Transit | 7 |
| Delayed Orders | 328 |
| On-Time Delivery | 83.1% |
| Packing-Stage Delays | 123 |
| Warehouse-Controlled Delays | 246 |
| Total Operational Cost | ₹762,668.45 |

### Major Observations

- Packing was the largest contributor to warehouse-stage delays.
- The period from 15–21 October experienced a concentration of order delays.
- Electronics and Toys & Games showed comparatively higher inventory-related risks.
- Evening shift had the highest orders per employee.
- Morning shift recorded the highest delay rate.
- Remote warehouse zones experienced higher late-delivery rates.

*All findings are based on the project's synthetic dataset and generated analytical assumptions.*

---

## Agentic Control Tower – Seven Specialist Agents

The Phase 2 application contains seven specialist agents coordinated through an orchestrator.

| Agent | Responsibility |
|---|---|
| Data Analysis Agent | Analyses warehouse performance and KPIs |
| Order Delay Investigation Agent | Investigates individual delayed orders |
| Bottleneck Detection Agent | Identifies operational bottlenecks |
| Shift Performance Agent | Analyses employee and shift performance |
| Inventory Shortage Agent | Identifies inventory-related risks |
| Operational Recommendation Agent | Suggests operational improvements |
| Automated Reporting Agent | Generates analytical reports |

### System Architecture

The Control Tower combines:

- FastAPI application layer
- Agent orchestration layer
- Seven specialist agents
- Deterministic Python analytical tools
- Human approval and audit logging
- n8n workflow automation blueprints

### Output Provenance

The application distinguishes between three types of outputs:

- 🟢 **COMPUTED:** Metrics calculated using Python.
- 🔵 **AI ANALYSIS:** AI-generated interpretation when live AI integration is configured; offline fallback is currently available.
- 🟡 **REQUIRES APPROVAL:** Recommendations or actions requiring human review.

**Human-in-the-Loop:** Operational approvals are recorded in an audit log. The system does not independently execute warehouse operations.

---

## Project Validation

### Phase 1 – Analytics Validation

- 61 independent validation checks.
- Dataset and KPI verification.
- Rule-based bottleneck detection validation.
- Power BI dashboard verification.

### Phase 2 – Control Tower Testing

- 125/125 development tests passed.
- Python analytical tool testing.
- Agent and routing tests.
- API testing.
- Human approval workflow checks.

*The two validation counts represent separate testing phases and are not combined.*

---

## Project Structure

The repository contains:

- Synthetic warehouse datasets.
- Python analysis scripts.
- Jupyter Notebook.
- Power BI dashboard files.
- Phase 1 validation materials.
- FastAPI Control Tower application.
- Seven specialist agents.
- Deterministic Python analytical tools.
- n8n workflow JSON blueprints.
- Documentation, reports, and presentations.
- Dashboard screenshots and visualisations.

---

## How to Run

### Phase 1 – Warehouse Analytics

1. Clone or download the repository.
2. Install Python and Jupyter Notebook.
3. Install the required dependencies:

   `pip install -r requirements.txt`

4. Open `warehouse_analysis.ipynb`.
5. Run the notebook cells.
6. Open `WarehouseDashboard.pbip` using Power BI Desktop.

### Phase 2 – Agentic Control Tower

1. Open the `control_tower` folder.
2. Install the dependencies specified for the Control Tower.
3. Start the FastAPI application using its configured startup command.
4. Open the application in your browser:

   `http://localhost:8000`

5. Explore the specialist agents, analytical outputs, and operational recommendations.

*Refer to the Control Tower setup documentation for its exact installation and startup instructions.*

---

## Project Deliverables

The `Documentation` folder contains the integrated academic submission:

- `Final_Integrated_Project_Report.docx`
- `Final_Integrated_Project_Report.pdf`
- `Final_Integrated_Presentation.pptx`

The repository also contains the original analysis notebook, synthetic dataset, Power BI dashboard, Control Tower source code, and supporting documentation.

---

## Project Team

**MBA – Operations & Business Analytics**

- Ishan Mishra
- Remee
- Nishu
- Taniya

**Institution:** IILM University, Greater Noida

---

## Limitations and Future Scope

### Current Limitations

- The dataset is synthetic and does not represent actual company operations.
- Bottleneck detection in Phase 1 uses predefined rules rather than a trained machine-learning model.
- Live Gemini API integration requires API configuration and has not yet been verified.
- n8n workflow files have been created and syntax-validated, but live execution remains pending.
- Operational recommendations require human review.

### Future Scope

- Integrate live warehouse management system data.
- Configure and validate live Gemini API integration.
- Execute and test n8n workflows.
- Introduce predictive analytics for delay forecasting.
- Develop real-time warehouse monitoring and alerting.
- Integrate inventory and order-management systems.

---

## Academic Disclaimer

This project was developed for academic purposes as part of the MBA programme in Operations and Business Analytics.

The project uses synthetic data and simulated operational scenarios. AI tools assisted in development, but analytical KPIs are calculated using Python-based processing and predefined rules. The Control Tower demonstrates an AI-assisted decision-support architecture; it is not a production-ready autonomous warehouse management system.
