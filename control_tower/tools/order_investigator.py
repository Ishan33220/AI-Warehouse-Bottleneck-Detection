"""
Single-order drill-down investigation logic.

Performs a multi-step investigation: looks up the order, compares every stage
to benchmarks, checks contextual factors, and finds similar delayed orders.
This is the tool behind Agent 2 (Order Delay Investigation).
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


def investigate_order(df: pd.DataFrame, order_id: str) -> Dict[str, Any]:
    """
    Multi-step investigation of a specific order.

    Steps:
    1. Retrieve the order row.
    2. Compare each stage time to its benchmark.
    3. Identify contextual factors (festive, trainee, inventory, zone).
    4. Cross-reference with delay reason column.
    5. Compare to similar orders.

    Returns a structured investigation report.
    """
    from config.settings import (
        STAGE_TIME_COLUMNS, NORMAL_STAGE_TIMES, TRAINEES,
        FESTIVE_START, FESTIVE_END,
    )

    order = df[df["Order_ID"] == order_id]
    if len(order) == 0:
        return {"found": False, "order_id": order_id,
                "message": f"Order {order_id} not found in the dataset."}

    row = order.iloc[0]

    # ── Step 1: Basic info ────────────────────────────────────────
    info: Dict[str, Any] = {
        "found": True,
        "order_id": order_id,
        "order_date": (
            str(row["Order_Date"].date())
            if hasattr(row["Order_Date"], "date") else str(row["Order_Date"])
        ),
        "shift": str(row["Shift"]),
        "location": str(row["Customer_Location"]),
        "zone": str(row["Delivery_Zone"]),
        "category": str(row["Product_Category"]),
        "priority": str(row["Order_Priority"]),
        "quantity": int(row["Order_Quantity"]),
        "status": str(row["Order_Status"]),
        "employee": str(row["Warehouse_Employee_ID"]),
        "inventory_status": str(row["Inventory_Status"]),
        "cost": float(row["Operational_Cost"]),
    }

    # ── Step 2: Stage-by-stage timing ─────────────────────────────
    stages: Dict[str, Any] = {}
    for stage_name, col in STAGE_TIME_COLUMNS.items():
        value = row[col]
        normal = NORMAL_STAGE_TIMES.get(stage_name)
        if pd.notna(value):
            entry: Dict[str, Any] = {"actual_minutes": round(float(value), 1)}
            if normal:
                entry["benchmark_minutes"] = normal
                entry["excess_minutes"] = round(float(value) - normal, 1)
                entry["excess_ratio"] = round(float(value) / normal, 2)
            stages[stage_name] = entry
        else:
            stages[stage_name] = {
                "actual_minutes": None,
                "reason": "Stage not reached (order cancelled or in transit)",
            }
    info["stage_analysis"] = stages

    # ── Step 3: Delay info ────────────────────────────────────────
    info["delay_status"] = str(row["Delay_Status"])
    info["delay_stage"] = str(row["Delay_Stage"])
    info["delay_reason"] = str(row["Delay_Reason"])

    if row["Delay_Status"] == "Delayed" and pd.notna(row["Total_Time_Minutes"]):
        info["total_time_minutes"] = float(row["Total_Time_Minutes"])
        info["sla_minutes"] = int(row["SLA_Minutes"])
        info["excess_over_sla_minutes"] = round(
            float(row["Total_Time_Minutes"]) - int(row["SLA_Minutes"]), 1
        )

    # ── Step 4: Contextual factors ────────────────────────────────
    factors = []
    order_date = pd.Timestamp(row["Order_Date"])
    if pd.Timestamp(FESTIVE_START) <= order_date <= pd.Timestamp(FESTIVE_END):
        factors.append("Order placed during festive week (2.3× volume surge)")
    if str(row["Warehouse_Employee_ID"]) in TRAINEES:
        factors.append(f"Assigned to trainee picker ({row['Warehouse_Employee_ID']}, ~30% slower)")
    if row["Inventory_Status"] == "Out of Stock":
        factors.append("Product was out of stock — required replenishment wait")
    elif row["Inventory_Status"] == "Low Stock":
        factors.append("Product was at low stock level")
    if row["Order_Priority"] == "Express":
        factors.append("Express priority — tighter SLA")
    if row["Delivery_Zone"] == "Remote":
        factors.append("Remote delivery zone — longer transit times expected")
    info["contextual_factors"] = factors

    # ── Step 5: Comparison with similar orders ────────────────────
    similar = df[
        (df["Product_Category"] == row["Product_Category"])
        & (df["Delivery_Zone"] == row["Delivery_Zone"])
        & (df["Order_Priority"] == row["Order_Priority"])
        & (df["Order_Status"] == "Delivered")
    ]
    if len(similar) > 0 and pd.notna(row.get("Total_Time_Minutes")):
        total = float(row["Total_Time_Minutes"])
        info["comparison"] = {
            "similar_orders_count": len(similar),
            "avg_total_time_minutes": round(float(similar["Total_Time_Minutes"].mean()), 1),
            "this_order_total_time": total,
            "percentile": round(
                float((similar["Total_Time_Minutes"] < total).mean()) * 100, 1
            ),
        }

    return info


def investigate_batch(df: pd.DataFrame, order_ids: list) -> list:
    """Investigate multiple orders at once."""
    return [investigate_order(df, oid) for oid in order_ids]


def find_similar_delayed_orders(df: pd.DataFrame, order_id: str,
                                 top_n: int = 5) -> pd.DataFrame:
    """Find delayed orders with similar characteristics (for pattern matching)."""
    order = df[df["Order_ID"] == order_id]
    if len(order) == 0:
        return pd.DataFrame()

    row = order.iloc[0]
    delayed = df[(df["Delay_Status"] == "Delayed") & (df["Order_ID"] != order_id)]
    if len(delayed) == 0:
        return pd.DataFrame()

    # Score similarity on multiple dimensions
    scores = pd.Series(0.0, index=delayed.index)
    if row["Delay_Stage"] not in ("Not Applicable", "No Delay"):
        scores += (delayed["Delay_Stage"] == row["Delay_Stage"]).astype(float) * 3
    scores += (delayed["Product_Category"] == row["Product_Category"]).astype(float) * 2
    scores += (delayed["Delivery_Zone"] == row["Delivery_Zone"]).astype(float) * 1
    scores += (delayed["Shift"] == row["Shift"]).astype(float) * 1

    top_idx = scores.nlargest(top_n).index
    cols = ["Order_ID", "Order_Date", "Delay_Stage", "Delay_Reason",
            "Product_Category", "Delivery_Zone", "Total_Time_Minutes"]
    return delayed.loc[top_idx, cols].copy()
