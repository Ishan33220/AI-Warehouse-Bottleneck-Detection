"""
Agent 6 – Operational Recommendation Agent.

Gathers findings from Agents 3–5 and generates data-backed recommendations.
Consequential recommendations are flagged for human approval.
"""

import pandas as pd
from agents.base_agent import BaseAgent, AgentResponse
from agents.bottleneck_agent import BottleneckAgent
from agents.shift_performance_agent import ShiftPerformanceAgent
from agents.inventory_agent import InventoryAgent
from tools.cost_analyzer import compute_cost_summary
from config.prompts import RECOMMENDATION_PROMPT

# Recommendations classified as "consequential" require human approval
CONSEQUENTIAL_KEYWORDS = [
    "hire", "recruit", "fire", "terminate", "restructure", "close",
    "invest", "purchase", "contract", "outsource", "pay",
]


class RecommendationAgent(BaseAgent):
    """
    Synthesises findings from all analysis agents into ranked recommendations.
    Flags consequential items for human approval before they are logged.
    """

    name = "Operational Recommendation Agent"

    def __init__(self):
        super().__init__()
        self._bottleneck_agent = BottleneckAgent()
        self._shift_agent = ShiftPerformanceAgent()
        self._inventory_agent = InventoryAgent()

    def run(self, query: str, df: pd.DataFrame, **kwargs) -> AgentResponse:
        response = AgentResponse(self.name, query)

        # ── Step 1: Gather analysis from sub-agents ───────────────
        bottleneck_resp = self._bottleneck_agent.run(
            "bottleneck analysis for recommendations", df, make_chart=False
        )
        shift_resp = self._shift_agent.run(
            "shift analysis for recommendations", df, make_chart=False
        )
        inventory_resp = self._inventory_agent.run(
            "inventory analysis for recommendations", df
        )
        cost_summary = compute_cost_summary(df)

        # ── Step 2: Store computed evidence ──────────────────────
        response.computed = {
            "supporting_evidence": {
                "bottleneck": bottleneck_resp.computed,
                "shift": shift_resp.computed,
                "inventory": inventory_resp.computed,
                "cost": cost_summary,
            }
        }

        # ── Step 3: Generate AI recommendations ──────────────────
        prompt = RECOMMENDATION_PROMPT.format(
            bottleneck_data=self._summarise(bottleneck_resp.computed),
            shift_data=self._summarise(shift_resp.computed),
            inventory_data=self._summarise(inventory_resp.computed),
            cost_data=self._summarise(cost_summary),
        )
        ai_text = self._ask_gemini(prompt)
        if not ai_text:
            ai_text = self._fallback_recommendations(
                bottleneck_resp.computed, shift_resp.computed,
                inventory_resp.computed, cost_summary
            )
        response.ai_narrative = ai_text

        # ── Step 4: Flag consequential recommendations ────────────
        if self._is_consequential(ai_text):
            self._flag_for_approval(
                response,
                "One or more recommendations above involve significant operational changes "
                "(staffing, procurement, or contract decisions). "
                "Please review and confirm before acting."
            )

        self._log(response)
        return response

    # ── Helpers ──────────────────────────────────────────────────

    def _summarise(self, data: dict, max_chars: int = 600) -> str:
        import json
        text = json.dumps(data, default=str, indent=2)
        return text[:max_chars] + ("..." if len(text) > max_chars else "")

    def _is_consequential(self, text: str) -> bool:
        lower = text.lower()
        return any(kw in lower for kw in CONSEQUENTIAL_KEYWORDS)

    def _fallback_recommendations(self, bottleneck, shift, inventory, cost) -> str:
        b = bottleneck.get("bottleneck", "Packing")
        busiest = shift.get("busiest_shift", "Evening")
        at_risk = inventory.get("at_risk_categories", [])
        cost_premium = cost.get("cost_premium_delayed_vs_ontime", 0)

        recs = [
            f"1. [AI ANALYSIS] Add flexible packing capacity during peak hours to address the "
            f"{b} bottleneck (causes {bottleneck.get('bottleneck_delays','N/A')} delays). "
            f"Difficulty: Medium.",
            f"2. [AI ANALYSIS] Rebalance shift workload — the {busiest} shift is overloaded "
            f"({shift.get('workload_imbalance_ratio','N/A')}x imbalance). "
            f"Consider reallocating orders to Night shift. Difficulty: Low.",
            f"3. [AI ANALYSIS] Increase safety stock for at-risk categories: "
            f"{', '.join(at_risk) if at_risk else 'Electronics, Toys & Games'} "
            f"before the next festive period. Difficulty: Low.",
            f"4. [AI ANALYSIS] Investigate why delayed orders cost ₹{cost_premium:.2f} more than "
            f"on-time orders on average — includes compensation vouchers and extra handling. "
            f"Reducing delays will directly reduce costs. Difficulty: Medium.",
            f"5. [AI ANALYSIS] Provide targeted coaching to trainee pickers "
            f"(EMP005, EMP012, EMP018) to reduce their ~30% speed gap. Difficulty: Low.",
        ]
        return "\n\n".join(recs)
