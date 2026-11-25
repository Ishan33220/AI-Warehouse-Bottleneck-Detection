"""
Operational cost analysis tools.

Breaks down costs by order status, dimension, and identifies anomalies.
"""

import pandas as pd
from typing import Dict, Any


def compute_cost_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Overall cost metrics."""
    total_cost = round(float(df["Operational_Cost"].sum()), 2)
    avg_cost = round(float(df["Operational_Cost"].mean()), 2)
    median_cost = round(float(df["Operational_Cost"].median()), 2)

    delivered = df[df["Order_Status"] == "Delivered"]
    cancelled = df[df["Order_Status"] == "Cancelled"]
    delayed = df[df["Delay_Status"] == "Delayed"]
    on_time = df[df["Delay_Status"] == "On Time"]

    avg_delayed = round(float(delayed["Operational_Cost"].mean()), 2) if len(delayed) else 0.0
    avg_on_time = round(float(on_time["Operational_Cost"].mean()), 2) if len(on_time) else 0.0

    return {
        "total_cost_rs": total_cost,
        "avg_cost_per_order": avg_cost,
        "median_cost_per_order": median_cost,
        "avg_cost_delivered": round(float(delivered["Operational_Cost"].mean()), 2),
        "avg_cost_cancelled": (
            round(float(cancelled["Operational_Cost"].mean()), 2) if len(cancelled) else 0.0
        ),
        "avg_cost_delayed": avg_delayed,
        "avg_cost_on_time": avg_on_time,
        "cost_premium_delayed_vs_ontime": round(avg_delayed - avg_on_time, 2),
    }


def compute_cost_by_dimension(df: pd.DataFrame, dimension: str) -> Dict[str, float]:
    """Average cost by any categorical column (e.g. Shift, Delivery_Zone)."""
    result = {}
    for val, group in df.groupby(dimension):
        result[str(val)] = round(float(group["Operational_Cost"].mean()), 2)
    return dict(sorted(result.items(), key=lambda x: -x[1]))


def compute_cost_by_category(df: pd.DataFrame) -> Dict[str, float]:
    """Average cost by product category."""
    return compute_cost_by_dimension(df, "Product_Category")


def compute_cost_by_zone(df: pd.DataFrame) -> Dict[str, float]:
    """Average cost by delivery zone."""
    return compute_cost_by_dimension(df, "Delivery_Zone")


def identify_high_cost_orders(df: pd.DataFrame,
                               multiplier: float = 2.0) -> pd.DataFrame:
    """Find orders with cost significantly above the mean."""
    avg = df["Operational_Cost"].mean()
    threshold = avg * multiplier
    return df[df["Operational_Cost"] > threshold].copy()
