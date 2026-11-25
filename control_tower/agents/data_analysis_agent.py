"""
Agent 1 – Warehouse Data Analysis Agent.

Loads the dataset, computes summary statistics, answers ad-hoc data questions.
"""

import pandas as pd
from agents.base_agent import BaseAgent, AgentResponse
from tools.kpi_calculator import compute_all_kpis, compute_core_kpis
from tools.data_loader import (
    filter_by_date_range, filter_by_shift, filter_by_zone,
    filter_by_category, filter_by_priority, filter_festive,
)
from config.prompts import DATA_ANALYSIS_PROMPT


class DataAnalysisAgent(BaseAgent):
    """Answers high-level questions about warehouse performance using live KPIs."""

    name = "Warehouse Data Analysis Agent"

    def run(self, query: str, df: pd.DataFrame, **kwargs) -> AgentResponse:
        """
        Parameters
        ----------
        query : str  — the user's question
        df    : pd.DataFrame  — the loaded (possibly filtered) dataset

        Optional kwargs:
            date_start, date_end, shift, zone, category, priority
        """
        response = AgentResponse(self.name, query)

        # Apply any filters passed by the orchestrator
        filtered = self._apply_filters(df, **kwargs)
        n_filtered = len(filtered)
        n_total = len(df)

        # ── Step 1: Compute all KPIs ─────────────────────────────
        kpis = compute_core_kpis(filtered)
        response.computed = {
            "records_analysed": n_filtered,
            "filter_applied": n_filtered < n_total,
            **kpis,
        }

        # ── Step 2: Generate AI narrative ────────────────────────
        prompt = DATA_ANALYSIS_PROMPT.format(
            computed_data=self._format_kpis(kpis, n_filtered, n_total)
        )
        response.ai_narrative = self._ask_gemini(prompt)
        if not response.ai_narrative:
            response.ai_narrative = self._fallback_narrative(kpis, n_filtered)

        self._log(response)
        return response

    # ── Helpers ──────────────────────────────────────────────────

    def _apply_filters(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        result = df.copy()
        if kwargs.get("date_start") and kwargs.get("date_end"):
            result = filter_by_date_range(result, kwargs["date_start"], kwargs["date_end"])
        if kwargs.get("shift"):
            result = filter_by_shift(result, kwargs["shift"])
        if kwargs.get("zone"):
            result = filter_by_zone(result, kwargs["zone"])
        if kwargs.get("category"):
            result = filter_by_category(result, kwargs["category"])
        if kwargs.get("priority"):
            result = filter_by_priority(result, kwargs["priority"])
        if kwargs.get("festive_only"):
            result = filter_festive(result)
        return result

    def _format_kpis(self, kpis: dict, n_filtered: int, n_total: int) -> str:
        scope = "full dataset" if n_filtered == n_total else f"filtered subset ({n_filtered}/{n_total} orders)"
        lines = [f"Scope: {scope}"]
        for k, v in kpis.items():
            lines.append(f"  {k.replace('_', ' ').title()}: {v}")
        return "\n".join(lines)

    def _fallback_narrative(self, kpis: dict, n: int) -> str:
        """Plain-text summary when Gemini is unavailable."""
        return (
            f"Analysed {n:,} orders. "
            f"On-time delivery: {kpis['on_time_delivery_pct']}%. "
            f"Delayed: {kpis['delayed_orders']}. "
            f"Avg packing: {kpis['avg_packing_minutes']} min. "
            f"Total cost: ₹{kpis['total_operational_cost_rs']:,.2f}."
        )
