"""
Inventory shortage analysis tools.

Analyses out-of-stock and low-stock patterns by category, time period,
and their impact on delays and cancellations.
"""

import pandas as pd
from typing import Dict, Any, List


def compute_inventory_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Overall inventory status breakdown."""
    total = len(df)
    available = int((df["Inventory_Status"] == "Available").sum())
    low_stock = int((df["Inventory_Status"] == "Low Stock").sum())
    oos = int((df["Inventory_Status"] == "Out of Stock").sum())

    return {
        "total_orders": total,
        "available": available,
        "low_stock": low_stock,
        "out_of_stock": oos,
        "shortage_pct": round(oos / total * 100, 1),
        "shortage_plus_low_pct": round((oos + low_stock) / total * 100, 1),
    }


def compute_shortage_by_category(df: pd.DataFrame, oos_only: bool = True) -> Dict[str, float]:
    """
    Inventory shortage % by product category.

    Parameters
    ----------
    oos_only : bool
        If True (default), counts only Out of Stock (matches kpi_summary.json).
        If False, includes Low Stock as well.
    """
    statuses = ["Out of Stock"] if oos_only else ["Out of Stock", "Low Stock"]
    result = {}
    for cat, group in df.groupby("Product_Category"):
        shortage = int(group["Inventory_Status"].isin(statuses).sum())
        result[str(cat)] = round(shortage / len(group) * 100, 1)
    return dict(sorted(result.items(), key=lambda x: -x[1]))


def compute_shortage_impact(df: pd.DataFrame) -> Dict[str, Any]:
    """Operational impact of inventory shortages on delays and cancellations."""
    oos = df[df["Inventory_Status"] == "Out of Stock"]
    low = df[df["Inventory_Status"] == "Low Stock"]
    avail = df[df["Inventory_Status"] == "Available"]

    # Cancellations driven by OOS
    oos_cancelled = int((oos["Order_Status"] == "Cancelled").sum())
    total_cancelled = int((df["Order_Status"] == "Cancelled").sum())

    # Delays attributed to the Inventory stage
    inv_delays = int(
        ((df["Delay_Status"] == "Delayed") & (df["Delay_Stage"] == "Inventory")).sum()
    )

    # Average inventory-check wait time comparison (delivered orders)
    oos_delivered = oos[oos["Order_Status"] == "Delivered"]
    avail_delivered = avail[avail["Order_Status"] == "Delivered"]

    return {
        "oos_orders": len(oos),
        "low_stock_orders": len(low),
        "oos_cancellations": oos_cancelled,
        "total_cancellations": total_cancelled,
        "oos_cancellation_rate_pct": (
            round(oos_cancelled / len(oos) * 100, 1) if len(oos) > 0 else 0.0
        ),
        "inventory_stage_delays": inv_delays,
        "avg_inventory_time_oos": (
            round(float(oos_delivered["Inventory_Check_Time_Minutes"].mean()), 1)
            if len(oos_delivered) > 0 else 0.0
        ),
        "avg_inventory_time_available": (
            round(float(avail_delivered["Inventory_Check_Time_Minutes"].mean()), 1)
            if len(avail_delivered) > 0 else 0.0
        ),
    }


def identify_at_risk_categories(df: pd.DataFrame,
                                 threshold_pct: float = 10.0,
                                 oos_only: bool = True) -> List[str]:
    """
    Return categories whose shortage rate exceeds the threshold.

    Parameters
    ----------
    threshold_pct : float
        Percentage threshold above which a category is considered at risk (default 10.0%).
    oos_only : bool
        If True (default), evaluates Out of Stock rate. If False, evaluates combined
        (Out of Stock + Low Stock) shortage rate.
    """
    shortage = compute_shortage_by_category(df, oos_only=oos_only)
    return [cat for cat, pct in shortage.items() if pct >= threshold_pct]
