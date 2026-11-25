"""
Agent 4 – Shift Performance Analysis Agent.

Analyses workload balance, picking/packing speed, and delay rate by shift.
"""

import pandas as pd
from agents.base_agent import BaseAgent, AgentResponse
from tools.shift_analyzer import compute_shift_metrics, compare_shifts, analyze_employee_performance
from tools.chart_generator import create_shift_comparison_chart
from config.prompts import SYSTEM_PROMPT


class ShiftPerformanceAgent(BaseAgent):
    """Analyses shift workload balance and surfaces staffing insights."""

    name = "Shift Performance Analysis Agent"

    def run(self, query: str, df: pd.DataFrame, **kwargs) -> AgentResponse:
        """
        Optional kwargs:
            make_chart   : bool — generate charts (default True)
            include_employees : bool — include per-employee breakdown (default False)
        """
        response = AgentResponse(self.name, query)

        # ── Compute shift metrics ─────────────────────────────────
        shift_comparison = compare_shifts(df)
        response.computed = shift_comparison

        # ── Optional: employee breakdown ──────────────────────────
        if kwargs.get("include_employees", False):
            employees = analyze_employee_performance(df)
            response.computed["employee_performance"] = employees

        # ── Charts ───────────────────────────────────────────────
        if kwargs.get("make_chart", True):
            try:
                metrics = shift_comparison["shift_metrics"]
                chart1 = create_shift_comparison_chart(metrics, "orders_per_employee",
                                                        "shift_workload.png")
                chart2 = create_shift_comparison_chart(metrics, "avg_packing_minutes",
                                                        "shift_packing.png")
                response.charts.extend([chart1, chart2])
            except Exception:
                pass

        # ── AI narrative ─────────────────────────────────────────
        prompt = self._build_prompt(shift_comparison)
        response.ai_narrative = self._ask_gemini(prompt)
        if not response.ai_narrative:
            response.ai_narrative = self._fallback_narrative(shift_comparison)

        self._log(response)
        return response

    # ── Helpers ──────────────────────────────────────────────────

    def _build_prompt(self, comparison: dict) -> str:
        lines = [
            "Analyse the following shift performance data for a warehouse operations manager.",
            "",
            "SHIFT DATA:",
        ]
        for s in comparison.get("shift_metrics", []):
            lines.append(
                f"  {s['shift']}: {s['orders']} orders, {s['employees']} employees, "
                f"{s['orders_per_employee']} orders/employee, "
                f"avg picking {s['avg_picking_minutes']} min, "
                f"avg packing {s['avg_packing_minutes']} min, "
                f"delay rate {s['delayed_pct']}%"
            )
        lines += [
            f"\nBusiest shift: {comparison.get('busiest_shift')}",
            f"Lightest shift: {comparison.get('lightest_shift')}",
            f"Workload imbalance ratio: {comparison.get('workload_imbalance_ratio')}x",
            "",
            "Identify: which shift is most strained, any workload imbalance, "
            "and which metric most urgently needs attention.",
        ]
        return "\n".join(lines)

    def _fallback_narrative(self, comparison: dict) -> str:
        busiest = comparison.get("busiest_shift", "N/A")
        ratio = comparison.get("workload_imbalance_ratio", "N/A")
        metrics = {m["shift"]: m for m in comparison.get("shift_metrics", [])}
        evening = metrics.get("Evening", {})
        return (
            f"The {busiest} shift is the busiest by orders per employee. "
            f"Workload imbalance ratio is {ratio}x between the busiest and lightest shifts. "
            f"Evening shift: {evening.get('orders_per_employee', 'N/A')} orders/employee, "
            f"{evening.get('delayed_pct', 'N/A')}% delay rate."
        )
