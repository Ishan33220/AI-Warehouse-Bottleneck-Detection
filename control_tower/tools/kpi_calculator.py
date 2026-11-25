"""
KPI calculations matching the original warehouse_analysis.ipynb and kpi_summary.json.

Every function here is DETERMINISTIC — same input data always gives the same output.
These are the "muscles" that agents call; agents only narrate, never invent numbers.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List


# ═══════════════════════════════════════════════════════════════════
# Core KPIs
# ═══════════════════════════════════════════════════════════════════

def compute_core_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute top-level KPIs matching the ``kpis`` block in kpi_summary.json.

    Returns dict with keys: total_orders, completed_orders_delivered,
    cancelled_orders, in_transit_orders, delayed_orders, on_time_delivery_pct,
    avg_picking_minutes, avg_packing_minutes, avg_delivery_hours,
    inventory_shortage_pct, total_operational_cost_rs.
    """
    total = len(df)
    delivered = len(df[df["Order_Status"] == "Delivered"])
    cancelled = len(df[df["Order_Status"] == "Cancelled"])
    in_transit = len(df[df["Order_Status"] == "In Transit"])

    delayed = len(df[df["Delay_Status"] == "Delayed"])
    on_time = len(df[df["Delay_Status"] == "On Time"])
    judged = on_time + delayed
    on_time_pct = round(on_time / judged * 100, 1) if judged > 0 else 0.0

    # Stage averages (NaN ignored automatically — cancelled/in-transit excluded)
    avg_picking = round(float(df["Picking_Time_Minutes"].mean()), 1)
    avg_packing = round(float(df["Packing_Time_Minutes"].mean()), 1)
    avg_delivery_hours = round(float(df["Delivery_Time_Minutes"].mean()) / 60, 1)

    # Inventory shortage = Out-of-Stock orders / total (matches headline KPI)
    oos_count = len(df[df["Inventory_Status"] == "Out of Stock"])
    shortage_pct = round(oos_count / total * 100, 1)

    total_cost = round(float(df["Operational_Cost"].sum()), 2)

    return {
        "total_orders": total,
        "completed_orders_delivered": delivered,
        "cancelled_orders": cancelled,
        "in_transit_orders": in_transit,
        "delayed_orders": delayed,
        "on_time_delivery_pct": on_time_pct,
        "avg_picking_minutes": avg_picking,
        "avg_packing_minutes": avg_packing,
        "avg_delivery_hours": avg_delivery_hours,
        "inventory_shortage_pct": shortage_pct,
        "total_operational_cost_rs": total_cost,
    }


# ═══════════════════════════════════════════════════════════════════
# Stage-level metrics
# ═══════════════════════════════════════════════════════════════════

def compute_stage_metrics(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Per-stage metrics matching the ``stages`` list in kpi_summary.json.

    For each stage: avg_minutes, median_minutes, delays_caused, share_of_delays_pct.
    """
    from config.settings import STAGE_TIME_COLUMNS, ALL_DELAY_STAGES

    delayed_df = df[df["Delay_Status"] == "Delayed"]
    total_delayed = len(delayed_df)

    stages = []
    for stage_name in ALL_DELAY_STAGES:
        col = STAGE_TIME_COLUMNS[stage_name]

        avg_min = round(float(df[col].mean()), 1)
        median_min = round(float(df[col].median()), 1)
        delays = int((delayed_df["Delay_Stage"] == stage_name).sum())
        share = round(delays / total_delayed * 100, 1) if total_delayed > 0 else 0.0

        stages.append({
            "stage": stage_name,
            "avg_minutes": avg_min,
            "median_minutes": median_min,
            "delays_caused": delays,
            "share_of_delays_pct": share,
        })

    return stages


# ═══════════════════════════════════════════════════════════════════
# Delay split (warehouse vs. courier)
# ═══════════════════════════════════════════════════════════════════

def compute_delay_split(df: pd.DataFrame) -> Dict[str, int]:
    """Warehouse-controlled vs. courier delay counts."""
    from config.settings import WAREHOUSE_STAGES

    delayed = df[df["Delay_Status"] == "Delayed"]
    warehouse = int(delayed["Delay_Stage"].isin(WAREHOUSE_STAGES).sum())
    courier = len(delayed) - warehouse

    return {
        "warehouse_controlled_delays": warehouse,
        "courier_delays": courier,
    }


# ═══════════════════════════════════════════════════════════════════
# Delay reasons
# ═══════════════════════════════════════════════════════════════════

def compute_top_delay_reasons(df: pd.DataFrame, top_n: int = 8) -> Dict[str, int]:
    """Count delay reasons, returning the top N as {reason: count}."""
    delayed = df[df["Delay_Status"] == "Delayed"]
    counts = delayed["Delay_Reason"].value_counts().head(top_n)
    return {str(k): int(v) for k, v in counts.items()}


# ═══════════════════════════════════════════════════════════════════
# Festive week comparison
# ═══════════════════════════════════════════════════════════════════

def compute_festive_comparison(df: pd.DataFrame) -> Dict[str, float]:
    """Compare festive week vs. other days."""
    from config.settings import FESTIVE_START, FESTIVE_END

    start = pd.Timestamp(FESTIVE_START)
    end = pd.Timestamp(FESTIVE_END)

    festive = df[(df["Order_Date"] >= start) & (df["Order_Date"] <= end)]
    other = df[(df["Order_Date"] < start) | (df["Order_Date"] > end)]

    festive_days = (end - start).days + 1   # 7
    other_days = df["Order_Date"].dt.date.nunique() - festive_days

    def _delayed_pct(subset: pd.DataFrame) -> float:
        d = int((subset["Delay_Status"] == "Delayed").sum())
        ot = int((subset["Delay_Status"] == "On Time").sum())
        return round(d / (d + ot) * 100, 1) if (d + ot) > 0 else 0.0

    return {
        "festive_orders_per_day": round(len(festive) / festive_days, 1),
        "other_orders_per_day": round(len(other) / other_days, 1),
        "festive_avg_packing_minutes": round(float(festive["Packing_Time_Minutes"].mean()), 1),
        "other_avg_packing_minutes": round(float(other["Packing_Time_Minutes"].mean()), 1),
        "festive_delayed_pct": _delayed_pct(festive),
        "other_delayed_pct": _delayed_pct(other),
    }


# ═══════════════════════════════════════════════════════════════════
# Breakdowns by dimension
# ═══════════════════════════════════════════════════════════════════

def compute_shortage_by_category(df: pd.DataFrame) -> Dict[str, float]:
    """
    Out-of-Stock percentage by product category.
    Matches ``shortage_pct_by_category`` in kpi_summary.json (OOS-only).
    Note: use inventory_analyzer.compute_shortage_by_category() for OOS+Low Stock combined.
    """
    result = {}
    for cat, group in df.groupby("Product_Category"):
        shortage = int((group["Inventory_Status"] == "Out of Stock").sum())
        result[str(cat)] = round(shortage / len(group) * 100, 1)
    return dict(sorted(result.items(), key=lambda x: -x[1]))


def compute_delayed_by_priority(df: pd.DataFrame) -> Dict[str, float]:
    """Delay percentage by order priority."""
    result = {}
    for pri, group in df.groupby("Order_Priority"):
        d = int((group["Delay_Status"] == "Delayed").sum())
        ot = int((group["Delay_Status"] == "On Time").sum())
        result[str(pri)] = round(d / (d + ot) * 100, 1) if (d + ot) > 0 else 0.0
    return dict(sorted(result.items(), key=lambda x: -x[1]))


def compute_delayed_by_zone(df: pd.DataFrame) -> Dict[str, float]:
    """Delay percentage by delivery zone."""
    result = {}
    for zone, group in df.groupby("Delivery_Zone"):
        d = int((group["Delay_Status"] == "Delayed").sum())
        ot = int((group["Delay_Status"] == "On Time").sum())
        result[str(zone)] = round(d / (d + ot) * 100, 1) if (d + ot) > 0 else 0.0
    return dict(sorted(result.items(), key=lambda x: -x[1]))


# ═══════════════════════════════════════════════════════════════════
# Full KPI summary (matches kpi_summary.json structure)
# ═══════════════════════════════════════════════════════════════════

def compute_all_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute every KPI in one call.  The returned dict mirrors the structure
    of ``kpi_summary.json`` so the two can be compared directly.
    """
    from config.settings import WAREHOUSE_STAGES

    kpis = compute_core_kpis(df)
    stages = compute_stage_metrics(df)
    delay_split = compute_delay_split(df)

    # Top warehouse bottleneck (excluding courier Delivery stage)
    wh_stages = [s for s in stages if s["stage"] in WAREHOUSE_STAGES]
    top_stage = max(wh_stages, key=lambda s: s["delays_caused"])["stage"]

    return {
        "kpis": kpis,
        "stages": stages,
        "top_delay_stage": top_stage,
        **delay_split,
        "top_delay_reasons": compute_top_delay_reasons(df),
        "festive_week_vs_other_days": compute_festive_comparison(df),
        "shortage_pct_by_category": compute_shortage_by_category(df),
        "delayed_pct_by_priority": compute_delayed_by_priority(df),
        "delayed_pct_by_zone": compute_delayed_by_zone(df),
    }
