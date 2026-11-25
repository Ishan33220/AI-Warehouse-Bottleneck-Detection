"""
Shift performance analysis tools.

Analyses workload balance, picking/packing speed, and delay rate across
Morning, Evening, and Night shifts.
"""

import pandas as pd
from typing import Dict, Any, List


def compute_shift_metrics(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Per-shift metrics matching the ``shifts`` block in kpi_summary.json.

    Note: excludes orders with Warehouse_Employee_ID == "Unassigned"
    to match the original notebook's shift analysis (8 orders excluded).
    """
    from config.settings import EMPLOYEE_ROSTER

    working_df = df[df["Warehouse_Employee_ID"] != "Unassigned"].copy()

    shifts = []
    for shift_name in ["Morning", "Evening", "Night"]:
        s = working_df[working_df["Shift"] == shift_name]
        n_employees = len(EMPLOYEE_ROSTER[shift_name])
        n_orders = len(s)

        delayed = int((s["Delay_Status"] == "Delayed").sum())
        on_time = int((s["Delay_Status"] == "On Time").sum())
        judged = delayed + on_time
        delayed_pct = round(delayed / judged * 100, 1) if judged > 0 else 0.0

        shifts.append({
            "shift": shift_name,
            "orders": n_orders,
            "employees": n_employees,
            "orders_per_employee": round(n_orders / n_employees, 1),
            "avg_picking_minutes": round(float(s["Picking_Time_Minutes"].mean()), 1),
            "avg_packing_minutes": round(float(s["Packing_Time_Minutes"].mean()), 1),
            "delayed_pct": delayed_pct,
        })

    return shifts


def compare_shifts(df: pd.DataFrame) -> Dict[str, Any]:
    """Compare shifts and surface imbalances."""
    metrics = compute_shift_metrics(df)

    busiest = max(metrics, key=lambda s: s["orders_per_employee"])
    lightest = min(metrics, key=lambda s: s["orders_per_employee"])
    highest_delay = max(metrics, key=lambda s: s["delayed_pct"])
    slowest_picking = max(metrics, key=lambda s: s["avg_picking_minutes"])
    slowest_packing = max(metrics, key=lambda s: s["avg_packing_minutes"])

    return {
        "shift_metrics": metrics,
        "busiest_shift": busiest["shift"],
        "lightest_shift": lightest["shift"],
        "highest_delay_rate_shift": highest_delay["shift"],
        "slowest_picking_shift": slowest_picking["shift"],
        "slowest_packing_shift": slowest_packing["shift"],
        "workload_imbalance_ratio": round(
            busiest["orders_per_employee"] / lightest["orders_per_employee"], 2
        ),
    }


def analyze_employee_performance(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Per-employee workload and speed metrics."""
    from config.settings import TRAINEES

    working_df = df[df["Warehouse_Employee_ID"] != "Unassigned"].copy()

    employees = []
    for emp_id, group in working_df.groupby("Warehouse_Employee_ID"):
        delayed_count = int((group["Delay_Status"] == "Delayed").sum())
        on_time_count = int((group["Delay_Status"] == "On Time").sum())
        judged = delayed_count + on_time_count

        employees.append({
            "employee_id": str(emp_id),
            "total_orders": len(group),
            "shift": str(group["Shift"].mode().iloc[0]) if len(group) > 0 else "Unknown",
            "is_trainee": str(emp_id) in TRAINEES,
            "avg_picking_minutes": round(float(group["Picking_Time_Minutes"].mean()), 1),
            "avg_packing_minutes": round(float(group["Packing_Time_Minutes"].mean()), 1),
            "delayed_count": delayed_count,
            "delay_rate_pct": round(delayed_count / judged * 100, 1) if judged > 0 else 0.0,
        })

    employees.sort(key=lambda e: -e["total_orders"])
    return employees
