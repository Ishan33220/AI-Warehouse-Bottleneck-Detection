"""
Agent 2 – Order Delay Investigation Agent.

Multi-step tool-use: retrieves an order, compares stage times to benchmarks,
checks contextual factors, cross-references the delay reason, and finds patterns.
"""

import pandas as pd
from agents.base_agent import BaseAgent, AgentResponse
from tools.order_investigator import investigate_order, find_similar_delayed_orders
from config.prompts import DELAY_INVESTIGATION_PROMPT


class DelayInvestigationAgent(BaseAgent):
    """Investigates why a specific order (or group of orders) was delayed."""

    name = "Order Delay Investigation Agent"

    def run(self, query: str, df: pd.DataFrame, **kwargs) -> AgentResponse:
        """
        Required kwargs:
            order_id : str  — the Order_ID to investigate (e.g. 'ORD-100547')

        Optional kwargs:
            show_similar : bool  — also find similar delayed orders (default True)
        """
        response = AgentResponse(self.name, query)
        order_id = kwargs.get("order_id", "").strip()

        if not order_id:
            response.error = "Please provide an order_id (e.g. 'ORD-100547')."
            return response

        # ── Step 1–4: Full investigation ─────────────────────────
        investigation = investigate_order(df, order_id)
        if not investigation["found"]:
            response.error = investigation["message"]
            return response

        response.computed = investigation

        # ── Step 5: Find similar delayed orders ──────────────────
        if kwargs.get("show_similar", True) and investigation["delay_status"] == "Delayed":
            similar_df = find_similar_delayed_orders(df, order_id, top_n=5)
            if not similar_df.empty:
                response.computed["similar_delayed_orders"] = similar_df.to_dict(orient="records")

        # ── Step 6: AI narrative ─────────────────────────────────
        stage_text = self._format_stages(investigation.get("stage_analysis", {}))
        factors_text = "\n".join(f"- {f}" for f in investigation.get("contextual_factors", []))
        order_text = self._format_order(investigation)

        prompt = DELAY_INVESTIGATION_PROMPT.format(
            order_data=order_text,
            stage_analysis=stage_text,
            factors=factors_text or "No special contextual factors identified.",
        )
        response.ai_narrative = self._ask_gemini(prompt)
        if not response.ai_narrative:
            response.ai_narrative = self._fallback_narrative(investigation)

        self._log(response)
        return response

    # ── Helpers ──────────────────────────────────────────────────

    def _format_order(self, inv: dict) -> str:
        lines = [
            f"Order ID: {inv['order_id']}",
            f"Date: {inv['order_date']}  Shift: {inv['shift']}",
            f"Category: {inv['category']}  Priority: {inv['priority']}  Zone: {inv['zone']}",
            f"Status: {inv['status']}  Delay: {inv['delay_status']}",
            f"Delay Stage: {inv.get('delay_stage')}  Reason: {inv.get('delay_reason')}",
            f"Employee: {inv['employee']}  Inventory: {inv['inventory_status']}",
        ]
        if "total_time_minutes" in inv:
            lines.append(
                f"Total time: {inv['total_time_minutes']} min  "
                f"SLA: {inv['sla_minutes']} min  "
                f"Excess: {inv['excess_over_sla_minutes']} min"
            )
        return "\n".join(lines)

    def _format_stages(self, stages: dict) -> str:
        lines = []
        for stage, data in stages.items():
            if data.get("actual_minutes") is not None:
                excess = data.get("excess_minutes", "N/A")
                bench = data.get("benchmark_minutes", "N/A")
                lines.append(
                    f"  {stage}: {data['actual_minutes']} min "
                    f"(benchmark: {bench}, excess: {excess})"
                )
            else:
                lines.append(f"  {stage}: {data.get('reason', 'N/A')}")
        return "\n".join(lines)

    def _fallback_narrative(self, inv: dict) -> str:
        if inv["delay_status"] == "Delayed":
            return (
                f"Order {inv['order_id']} was delayed at the {inv['delay_stage']} stage. "
                f"Reason recorded: {inv['delay_reason']}. "
                f"Contextual factors: {'; '.join(inv.get('contextual_factors', ['None identified']))}."
            )
        elif inv["status"] == "Cancelled":
            return f"Order {inv['order_id']} was cancelled before processing was complete."
        else:
            return f"Order {inv['order_id']} was delivered on time."
