"""
Agent 5 – Inventory Shortage Analysis Agent.

Analyses out-of-stock and low-stock patterns by category, time period,
and their impact on delays and cancellations.
"""

import pandas as pd
from agents.base_agent import BaseAgent, AgentResponse
from tools.inventory_analyzer import (
    compute_inventory_summary, compute_shortage_by_category,
    compute_shortage_impact, identify_at_risk_categories,
)
from tools.data_loader import filter_festive, filter_non_festive
from config.settings import SHORTAGE_ALERT_PCT


class InventoryAgent(BaseAgent):
    """Analyses inventory shortage patterns and their operational impact."""

    name = "Inventory Shortage Analysis Agent"

    def run(self, query: str, df: pd.DataFrame, **kwargs) -> AgentResponse:
        """
        Optional kwargs:
            compare : bool — compare festive vs. non-festive shortage (default False)
        """
        response = AgentResponse(self.name, query)

        # ── Core analysis ─────────────────────────────────────────
        summary = compute_inventory_summary(df)
        by_category = compute_shortage_by_category(df, oos_only=True)
        impact = compute_shortage_impact(df)
        at_risk = identify_at_risk_categories(df, threshold_pct=SHORTAGE_ALERT_PCT)

        response.computed = {
            "inventory_summary": summary,
            "shortage_pct_by_category": by_category,
            "operational_impact": impact,
            "at_risk_categories": at_risk,
        }

        # ── Optional: festive comparison ──────────────────────────
        if kwargs.get("compare", False):
            festive = filter_festive(df)
            normal = filter_non_festive(df)
            response.computed["festive_shortage"] = compute_inventory_summary(festive)
            response.computed["normal_shortage"] = compute_inventory_summary(normal)

        # ── AI narrative ─────────────────────────────────────────
        prompt = self._build_prompt(summary, by_category, impact, at_risk)
        response.ai_narrative = self._ask_gemini(prompt)
        if not response.ai_narrative:
            response.ai_narrative = self._fallback_narrative(summary, by_category, at_risk)

        self._log(response)
        return response

    # ── Helpers ──────────────────────────────────────────────────

    def _build_prompt(self, summary, by_category, impact, at_risk) -> str:
        cats = "\n".join(f"  {c}: {p}% OOS" for c, p in by_category.items())
        return (
            f"Analyse the following inventory shortage data for a warehouse manager.\n\n"
            f"SUMMARY:\n"
            f"  Total orders: {summary['total_orders']}\n"
            f"  Out of Stock: {summary['out_of_stock']} ({summary['shortage_pct']}%)\n"
            f"  Low Stock: {summary['low_stock']}\n\n"
            f"SHORTAGE BY CATEGORY (OOS only):\n{cats}\n\n"
            f"OPERATIONAL IMPACT:\n"
            f"  OOS cancellations: {impact['oos_cancellations']} "
            f"({impact['oos_cancellation_rate_pct']}% of OOS orders)\n"
            f"  Inventory-stage delays: {impact['inventory_stage_delays']}\n"
            f"  Avg inventory wait (OOS): {impact['avg_inventory_time_oos']} min vs "
            f"{impact['avg_inventory_time_available']} min (available)\n\n"
            f"AT-RISK CATEGORIES (OOS > {SHORTAGE_ALERT_PCT}%): {', '.join(at_risk) or 'None'}\n\n"
            f"Provide: 1) Assessment of severity, 2) Which categories need immediate attention, "
            f"3) Impact on customer experience."
        )

    def _fallback_narrative(self, summary, by_category, at_risk) -> str:
        worst = list(by_category.items())[0] if by_category else ("N/A", 0)
        return (
            f"Inventory shortage rate: {summary['shortage_pct']}% of orders hit an OOS item. "
            f"Worst category: {worst[0]} at {worst[1]}% OOS rate. "
            f"At-risk categories (>{SHORTAGE_ALERT_PCT}%): "
            f"{', '.join(at_risk) if at_risk else 'None'}."
        )
