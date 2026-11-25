"""
Central configuration for the Warehouse Operations Control Tower.
All paths, business constants, and thresholds live here.
"""

import os
from pathlib import Path

# Try to load .env; fall back gracefully if python-dotenv is not installed
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# ═══════════════════════════════════════════════════════════════════
# Project Paths
# ═══════════════════════════════════════════════════════════════════
CONTROL_TOWER_DIR = Path(__file__).resolve().parent.parent          # control_tower/
PROJECT_ROOT = CONTROL_TOWER_DIR.parent                            # AI-Warehouse-Bottleneck-Detection/
DATASET_PATH = PROJECT_ROOT / "warehouse_orders.csv"               # clean master dataset
DATASET_RAW_PATH = PROJECT_ROOT / "warehouse_orders_raw.csv"       # messy raw dataset
KPI_REFERENCE_PATH = PROJECT_ROOT / "kpi_summary.json"             # pre-computed KPI reference
OUTPUTS_DIR = CONTROL_TOWER_DIR / "outputs"
LOGS_DIR = CONTROL_TOWER_DIR / "logs"

# ═══════════════════════════════════════════════════════════════════
# Business Constants (from generate_dataset.py)
# ═══════════════════════════════════════════════════════════════════
FESTIVE_START = "2026-10-15"
FESTIVE_END = "2026-10-21"
DATA_EXPORT_DATE = "2026-11-03"

# Trainee pickers (~30 % slower)
TRAINEES = {"EMP005", "EMP012", "EMP018"}

# Employee roster by shift (from generate_dataset.py)
EMPLOYEE_ROSTER = {
    "Morning": [f"EMP{n:03d}" for n in range(1, 8)],     # EMP001-EMP007 (7)
    "Evening": [f"EMP{n:03d}" for n in range(8, 15)],     # EMP008-EMP014 (7)
    "Night":   [f"EMP{n:03d}" for n in range(15, 21)],    # EMP015-EMP020 (6)
}

# Stage classifications
WAREHOUSE_STAGES = ["Receiving", "Inventory", "Picking", "Packing", "Dispatch"]
COURIER_STAGES = ["Delivery"]
ALL_DELAY_STAGES = WAREHOUSE_STAGES + COURIER_STAGES

# Map stage names → CSV column names
STAGE_TIME_COLUMNS = {
    "Receiving":  "Receiving_Time_Minutes",
    "Inventory":  "Inventory_Check_Time_Minutes",
    "Picking":    "Picking_Time_Minutes",
    "Packing":    "Packing_Time_Minutes",
    "Dispatch":   "Dispatch_Time_Minutes",
    "Delivery":   "Delivery_Time_Minutes",
}

# Normal (benchmark) stage times in minutes (from generate_dataset.py delay logic)
NORMAL_STAGE_TIMES = {
    "Receiving": 7,
    "Inventory": 7,
    "Picking":   30,
    "Packing":   15,
    "Dispatch":  35,
    # Delivery normal varies by priority+zone, handled separately
}

# Delivery benchmark by (priority, zone) — from generate_dataset.py
# Value = median_delivery × 1.08  (the threshold used for delay-stage attribution)
DELIVERY_NORMAL = {
    ("Express",  "Metro"):  756,   ("Express",  "Tier-2"): 1026,  ("Express",  "Remote"): 1350,
    ("Standard", "Metro"):  1836,  ("Standard", "Tier-2"): 2484,  ("Standard", "Remote"): 3348,
    ("Economy",  "Metro"):  2808,  ("Economy",  "Tier-2"): 3780,  ("Economy",  "Remote"): 4968,
}

# ═══════════════════════════════════════════════════════════════════
# AI Configuration
# ═══════════════════════════════════════════════════════════════════
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ═══════════════════════════════════════════════════════════════════
# Alert Thresholds
# ═══════════════════════════════════════════════════════════════════
DELAY_RATE_ALERT_PCT = 15.0        # Flag if delay rate > this
SHORTAGE_ALERT_PCT = 10.0          # Flag if stock-out rate > this per category
COST_ANOMALY_MULTIPLIER = 2.0     # Flag if order cost > this × average
