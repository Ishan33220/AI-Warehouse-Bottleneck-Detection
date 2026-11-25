"""
Agent 3 – Bottleneck Detection Agent.

Identifies and ranks bottleneck stages, optionally comparing periods or
drilling into causes behind a specific stage.
"""

import pandas as pd
from agents.base_agent import BaseAgent, AgentResponse
from tools.bottleneck_detector import (
    detect_bottleneck, rank_stages_by_delays,
    compute_warehouse_delay_share, analyze_bottleneck_causes,
    compare_bottlenecks,
)
from tools.chart_generator import create_stage_delay_chart
from tools.data_loader import filter_festive, filter_non_festive
from config.prompts import BOTTLENECK_ANALYSIS_PROMPT


class BottleneckAgent(BaseAgent):
    """Identifies the warehouse bottleneck and explains its operational causes."""

    name = "Bottleneck Detection Agent"

    def run(self, query: str, df: pd.DataFrame, **kwargs) -> AgentResponse:
        """
        Optional kwargs:
            stage     : str   — drill into a specific stage's causes
            compare   : bool  — compare festive vs. non-festive period
            make_chart: bool  — generate delay chart (default True)
        """
        response = AgentResponse(self.name, query)

        # ── Core detection ────────────────────────────────────────
        bottleneck = detect_bottleneck(df, scope="warehouse")
        ranked = rank_stages_by_delays(df)
        share = compute_warehouse_delay_share(df)

        response.computed = {
            **bottleneck,
            "warehouse_delay_share": share,
            "stage_ranking": ranked,
        }

        # ── Optional: cause drill-down ────────────────────────────
        stage = kwargs.get("stage") or bottleneck.get("bottleneck")
        causes = analyze_bottleneck_causes(df, stage)
        response.computed["cause_analysis"] = causes

        # ── Optional: festive comparison ──────────────────────────
        if kwargs.get("compare", False):
            comp = compare_bottlenecks(
                df,
                "Festive Week", filter_festive(df),
                "Normal Period", filter_non_festive(df),
            )
            response.computed["period_comparison"] = comp

        # ── Chart ─────────────────────────────────────────────────
        if kwargs.get("make_chart", True) and ranked:
            try:
                chart_path = create_stage_delay_chart(ranked)
                response.charts.append(chart_path)
            except Exception as e:
                pass  # Chart failure is non-fatal

        # ── AI narrative ─────────────────────────────────────────
        prompt = BOTTLENECK_ANALYSIS_PROMPT.format(
            bottleneck_data=self._format_bottleneck(bottleneck, share),
            stage_ranking=self._format_ranking(ranked),
        )
        response.ai_narrative = self._ask_gemini(prompt)
        if not response.ai_narrative:
            response.ai_narrative = self._fallback_narrative(bottleneck, share)

        self._log(response)
        return response

    # ── Helpers ──────────────────────────────────────────────────

    def _format_bottleneck(self, b: dict, share: dict) -> str:
        return (
            f"Top warehouse bottleneck: {b.get('bottleneck')} "
            f"({b.get('bottleneck_delays')} delays, {b.get('bottleneck_share_pct')}% of all delays)\n"
            f"Total delayed orders: {b.get('total_delayed')}\n"
            f"Warehouse-controlled delays: {share.get('warehouse_delays')} "
            f"({share.get('warehouse_share_pct')}%)\n"
            f"Courier delays: {share.get('courier_delays')}"
        )

    def _format_ranking(self, ranked: list) -> str:
        lines = []
        for s in ranked:
            lines.append(
                f"  {s['stage']}: {s['delays_caused']} delays "
                f"({s['share_of_delays_pct']}%), avg {s['avg_time_minutes']} min"
            )
        return "\n".join(lines)

    def _fallback_narrative(self, b: dict, share: dict) -> str:
        return (
            f"The primary warehouse bottleneck is {b.get('bottleneck')}, "
            f"causing {b.get('bottleneck_delays')} out of {b.get('total_delayed')} delays "
            f"({b.get('bottleneck_share_pct')}%). "
            f"{share.get('warehouse_share_pct')}% of all delays are warehouse-controlled."
        )
