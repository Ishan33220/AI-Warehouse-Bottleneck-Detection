"""
Report generation tools.

Assembles KPI data, charts, and analysis into Markdown or JSON reports.
PDF export via WeasyPrint is optional (Phase 4).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


def generate_markdown_report(kpi_data: Dict[str, Any],
                              title: str = "Warehouse Operations Report") -> str:
    """Generate a Markdown report from a full KPI data dict."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    kpis = kpi_data.get("kpis", {})

    lines = [
        f"# {title}",
        f"**Generated:** {ts}  ",
        f"**Data source:** warehouse_orders.csv (Synthetic data)",
        "",
        "---",
        "",
        "## Key Performance Indicators",
        "",
        "| KPI | Value |",
        "|-----|-------|",
        f"| Total Orders | {kpis.get('total_orders', 'N/A'):,} |",
        f"| Delivered | {kpis.get('completed_orders_delivered', 'N/A'):,} |",
        f"| Cancelled | {kpis.get('cancelled_orders', 'N/A'):,} |",
        f"| In Transit | {kpis.get('in_transit_orders', 'N/A'):,} |",
        f"| Delayed Orders | {kpis.get('delayed_orders', 'N/A'):,} |",
        f"| On-Time Delivery % | {kpis.get('on_time_delivery_pct', 'N/A')}% |",
        f"| Avg Picking Time | {kpis.get('avg_picking_minutes', 'N/A')} min |",
        f"| Avg Packing Time | {kpis.get('avg_packing_minutes', 'N/A')} min |",
        f"| Avg Delivery Time | {kpis.get('avg_delivery_hours', 'N/A')} hours |",
        f"| Inventory Shortage | {kpis.get('inventory_shortage_pct', 'N/A')}% |",
        f"| Total Cost | ₹{kpis.get('total_operational_cost_rs', 0):,.2f} |",
        "",
        "---",
        "",
        "## Bottleneck Analysis",
        "",
        f"**Top Bottleneck Stage:** {kpi_data.get('top_delay_stage', 'N/A')}  ",
        f"**Warehouse-Controlled Delays:** {kpi_data.get('warehouse_controlled_delays', 'N/A')}  ",
        f"**Courier Delays:** {kpi_data.get('courier_delays', 'N/A')}",
        "",
    ]

    # Stage table
    stages = kpi_data.get("stages", [])
    if stages:
        lines.extend([
            "| Stage | Delays | Share % | Avg Time (min) | Median (min) |",
            "|-------|--------|---------|----------------|--------------|",
        ])
        for s in stages:
            lines.append(
                f"| {s['stage']} | {s['delays_caused']} | {s['share_of_delays_pct']}% "
                f"| {s['avg_minutes']} | {s['median_minutes']} |"
            )

    # Delay reasons
    reasons = kpi_data.get("top_delay_reasons", {})
    if reasons:
        lines.extend(["", "### Top Delay Reasons", ""])
        for reason, count in reasons.items():
            lines.append(f"- {reason}: **{count}**")

    lines.extend([
        "",
        "---",
        "",
        "🟢 All numbers above are **[COMPUTED]** from the dataset using Python.",
    ])

    return "\n".join(lines)


def save_report(content: str, filename: str = "report.md") -> str:
    """Save a report string to the outputs directory. Returns the path."""
    from config.settings import OUTPUTS_DIR
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    return str(path)


def save_kpi_snapshot(kpi_data: Dict[str, Any],
                       filename: str = "kpi_snapshot.json") -> str:
    """Save KPI data as a JSON file. Returns the path."""
    from config.settings import OUTPUTS_DIR
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(kpi_data, f, indent=2, default=str)
    return str(path)
