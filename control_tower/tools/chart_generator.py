"""
Chart generation tools for warehouse analysis.

Creates publication-quality charts using Matplotlib.
Expanded with Plotly interactive charts in Phase 3/4.
"""

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server use
import matplotlib.pyplot as plt
from typing import List, Optional, Dict, Any
from pathlib import Path


def _ensure_output_dir() -> Path:
    """Create and return the outputs directory."""
    from config.settings import OUTPUTS_DIR
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUTS_DIR


def create_bar_chart(
    labels: List[str],
    values: List[float],
    title: str,
    xlabel: str = "",
    ylabel: str = "",
    color: str = "#1565c0",
    highlight_index: Optional[int] = None,
    highlight_color: str = "#c62828",
    filename: Optional[str] = None,
) -> str:
    """Create a vertical bar chart and save to file. Returns the file path."""
    output_dir = _ensure_output_dir()

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [highlight_color if i == highlight_index else color
              for i in range(len(labels))]
    ax.bar(labels, values, color=colors)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    if filename is None:
        filename = title.lower().replace(" ", "_").replace("/", "_") + ".png"
    path = output_dir / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def create_stage_delay_chart(stage_data: List[Dict[str, Any]],
                              filename: str = "delays_by_stage.png") -> str:
    """
    Create the delays-by-stage horizontal bar chart.

    Red = top warehouse bottleneck, blue = other warehouse stages, grey = courier.
    """
    from config.settings import WAREHOUSE_STAGES

    stages = [s["stage"] for s in stage_data]
    delays = [s["delays_caused"] for s in stage_data]

    # Identify the top warehouse bottleneck for highlighting
    wh_data = [s for s in stage_data if s["stage"] in WAREHOUSE_STAGES]
    top_wh = max(wh_data, key=lambda s: s["delays_caused"])["stage"] if wh_data else None

    colors = []
    for s in stages:
        if s == top_wh:
            colors.append("#c62828")   # Red for bottleneck
        elif s in WAREHOUSE_STAGES:
            colors.append("#1565c0")   # Blue for warehouse stages
        else:
            colors.append("#757575")   # Grey for courier

    output_dir = _ensure_output_dir()
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(stages, delays, color=colors)
    ax.set_title("Delays by Operational Stage", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Delays")
    ax.invert_yaxis()

    for bar, d in zip(bars, delays):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                str(d), va="center", fontsize=10)

    plt.tight_layout()
    path = output_dir / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def create_shift_comparison_chart(shift_metrics: List[Dict[str, Any]],
                                   metric: str = "orders_per_employee",
                                   filename: Optional[str] = None) -> str:
    """Create a bar chart comparing a metric across shifts."""
    labels = [s["shift"] for s in shift_metrics]
    values = [s[metric] for s in shift_metrics]
    title = f"{metric.replace('_', ' ').title()} by Shift"
    if filename is None:
        filename = f"shift_{metric}.png"
    return create_bar_chart(labels, values, title, ylabel=metric.replace("_", " "),
                            filename=filename)
