"""
Rule-based bottleneck detection logic.

Reimplements the same delay-stage ranking and attribution from
generate_dataset.py and warehouse_analysis.ipynb.
"""

import pandas as pd
from typing import Dict, Any, List, Optional


def detect_bottleneck(df: pd.DataFrame, scope: str = "warehouse") -> Dict[str, Any]:
    """
    Identify the top bottleneck stage.

    Parameters
    ----------
    df : DataFrame
        The warehouse orders dataset (or a filtered subset).
    scope : str
        "warehouse" excludes the Delivery stage (courier-controlled).
        "all" includes every stage.

    Returns
    -------
    dict with bottleneck stage name, counts, and share.
    """
    from config.settings import WAREHOUSE_STAGES, ALL_DELAY_STAGES

    delayed = df[df["Delay_Status"] == "Delayed"]
    if len(delayed) == 0:
        return {"bottleneck": None, "total_delayed": 0,
                "message": "No delayed orders in this selection."}

    stages_to_check = WAREHOUSE_STAGES if scope == "warehouse" else ALL_DELAY_STAGES

    stage_counts = {}
    for stage in stages_to_check:
        stage_counts[stage] = int((delayed["Delay_Stage"] == stage).sum())

    top_stage = max(stage_counts, key=stage_counts.get)
    total_delayed = len(delayed)

    return {
        "bottleneck": top_stage,
        "bottleneck_delays": stage_counts[top_stage],
        "total_delayed": total_delayed,
        "bottleneck_share_pct": round(stage_counts[top_stage] / total_delayed * 100, 1),
        "stage_delays": stage_counts,
        "scope": scope,
    }


def compute_warehouse_delay_share(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute what fraction of all delays originate inside the warehouse."""
    from config.settings import WAREHOUSE_STAGES

    delayed = df[df["Delay_Status"] == "Delayed"]
    if len(delayed) == 0:
        return {"warehouse_share_pct": 0.0, "warehouse_delays": 0,
                "courier_delays": 0, "total_delays": 0}

    wh = int(delayed["Delay_Stage"].isin(WAREHOUSE_STAGES).sum())
    total = len(delayed)

    return {
        "warehouse_share_pct": round(wh / total * 100, 1),
        "warehouse_delays": wh,
        "courier_delays": total - wh,
        "total_delays": total,
    }


def rank_stages_by_delays(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Rank all stages by number of delays caused (descending)."""
    from config.settings import ALL_DELAY_STAGES, STAGE_TIME_COLUMNS

    delayed = df[df["Delay_Status"] == "Delayed"]
    total_delayed = len(delayed)

    result = []
    for stage in ALL_DELAY_STAGES:
        count = int((delayed["Delay_Stage"] == stage).sum())
        col = STAGE_TIME_COLUMNS[stage]
        result.append({
            "stage": stage,
            "delays_caused": count,
            "share_of_delays_pct": round(count / total_delayed * 100, 1) if total_delayed else 0.0,
            "avg_time_minutes": round(float(df[col].mean()), 1),
            "median_time_minutes": round(float(df[col].median()), 1),
        })

    result.sort(key=lambda x: -x["delays_caused"])
    return result


def analyze_bottleneck_causes(df: pd.DataFrame,
                               stage: Optional[str] = None) -> Dict[str, Any]:
    """
    Deep-dive into the causes behind a specific bottleneck stage.

    If *stage* is None, automatically uses the top warehouse bottleneck.
    """
    if stage is None:
        result = detect_bottleneck(df)
        stage = result.get("bottleneck")
        if stage is None:
            return {"stage": None, "message": "No bottleneck detected."}

    from config.settings import STAGE_TIME_COLUMNS

    delayed = df[(df["Delay_Status"] == "Delayed") & (df["Delay_Stage"] == stage)]

    # Delay reasons at this stage
    reasons = {str(k): int(v) for k, v in delayed["Delay_Reason"].value_counts().items()}

    report: Dict[str, Any] = {
        "stage": stage,
        "total_delays_at_stage": len(delayed),
        "reasons": reasons,
    }

    # Compare timing for delayed vs. all orders at this stage
    col = STAGE_TIME_COLUMNS.get(stage)
    if col:
        all_times = df[col].dropna()
        delayed_times = delayed[col].dropna()
        report["avg_time_all_orders"] = round(float(all_times.mean()), 1)
        report["avg_time_delayed_orders"] = (
            round(float(delayed_times.mean()), 1) if len(delayed_times) > 0 else None
        )
        report["median_time_all_orders"] = round(float(all_times.median()), 1)
        report["median_time_delayed_orders"] = (
            round(float(delayed_times.median()), 1) if len(delayed_times) > 0 else None
        )

    # Breakdowns
    report["by_shift"] = {str(k): int(v) for k, v in delayed["Shift"].value_counts().items()}
    report["by_zone"] = {str(k): int(v) for k, v in delayed["Delivery_Zone"].value_counts().items()}
    report["by_category"] = {str(k): int(v) for k, v in delayed["Product_Category"].value_counts().items()}

    return report


def compare_bottlenecks(df: pd.DataFrame,
                         filter_a_label: str, filter_a_df: pd.DataFrame,
                         filter_b_label: str, filter_b_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compare bottleneck patterns between two subsets (e.g., festive vs. normal).
    """
    a = detect_bottleneck(filter_a_df)
    b = detect_bottleneck(filter_b_df)

    return {
        filter_a_label: a,
        filter_b_label: b,
        "same_bottleneck": a.get("bottleneck") == b.get("bottleneck"),
    }
