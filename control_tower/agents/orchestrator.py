"""
Orchestrator – routes natural-language user queries to the right agent.

Uses keyword/intent matching to dispatch. In Phase 3 this is called by
the FastAPI web interface.
"""

import re
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from agents.base_agent import AgentResponse
from agents.data_analysis_agent import DataAnalysisAgent
from agents.delay_investigation_agent import DelayInvestigationAgent
from agents.bottleneck_agent import BottleneckAgent
from agents.shift_performance_agent import ShiftPerformanceAgent
from agents.inventory_agent import InventoryAgent
from agents.recommendation_agent import RecommendationAgent
from agents.reporting_agent import ReportingAgent


# ── Intent patterns (order matters: more specific first) ─────────
# NOTE: patterns are matched against the ORIGINAL query (not lowercased)
#       using re.IGNORECASE, so ORD- uppercase is preserved for extraction.
INTENT_PATTERNS = [
    # Order investigation — ORD- pattern uses re.IGNORECASE flag at match time
    (r"\bORD-\d+\b", "investigate_order"),
    (r"\binvestigat(e|ion)\b", "investigate_order"),
    (r"\bwhy\b.*\bdelay(ed)?\b|\bdelay(ed)?\b.*\bwhy\b", "investigate_order"),

    # Bottleneck
    (r"\bbottleneck\b", "bottleneck"),
    (r"\bwhich stage\b|\bdelay stage\b", "bottleneck"),
    (r"\bwarehouse.controlled\b|\bshare.*delay\b|\bdelay.*share\b", "bottleneck"),
    (r"\bcompare.*period\b|\bfestive.*normal\b|\bnormal.*festive\b", "bottleneck"),

    # Shift
    (r"\bshift\b|\bmorning\b|\bevening\b|\bnight\b", "shift"),
    (r"\bworkload\b|\bemployee\b|\bpicker\b|\bstaff\b", "shift"),

    # Inventory
    (r"\binventor(y|ies)\b|\bstock.?out(s)?\b|\bout.of.stock\b|\blow.?stock\b", "inventory"),
    (r"\bshortage\b|\bcancellation(s)?\b", "inventory"),

    # Report  — \bsummar removed; only explicit report keywords here
    (r"\breport\b|\bgenerate\b.*\breport\b", "report"),
    (r"\bdaily\b.*\breport\b|\bweekly\b.*\breport\b", "report"),

    # Recommendations
    (r"\brecommend(ation)?s?\b|\bsuggestion?s?\b|\bimprove\b|\baction\b", "recommendations"),
    (r"\bwhat should\b|\bwhat to do\b|\bhow to fix\b", "recommendations"),

    # Data analysis (default) — summary now lives here, not in report
    (r"\bkpi\b|\bperformance\b|\bstat(istic)?s?\b|\boverview\b|\bsummar(y|ise|ize)\b", "data_analysis"),
    (r"\bon.?time\b|\bdelivery\b|\bcost\b|\btotal.?orders\b", "data_analysis"),
]


class Orchestrator:
    """
    Routes user queries to the appropriate specialist agent.

    Usage:
        orch = Orchestrator()
        orch.load_data()          # loads the dataset
        response = orch.dispatch("Why was ORD-100547 delayed?")
    """

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._agents = {
            "data_analysis":    DataAnalysisAgent(),
            "investigate_order": DelayInvestigationAgent(),
            "bottleneck":       BottleneckAgent(),
            "shift":            ShiftPerformanceAgent(),
            "inventory":        InventoryAgent(),
            "recommendations":  RecommendationAgent(),
            "report":           ReportingAgent(),
        }

    # ── Data loading ─────────────────────────────────────────────

    def load_data(self, path: Optional[str] = None, force_reload: bool = False):
        """Load (or reload) the dataset into memory."""
        from tools.data_loader import load_dataset
        self._df = load_dataset(path=path, force_reload=force_reload)
        return self

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            self.load_data()
        return self._df

    # ── Dispatch ─────────────────────────────────────────────────

    def dispatch(self, query: str, **kwargs) -> AgentResponse:
        """
        Parse the query, identify intent, extract parameters, run the agent.

        Returns an AgentResponse with computed data and AI narrative.
        """
        intent = self._classify_intent(query)
        agent_kwargs = self._extract_params(query, intent, **kwargs)
        agent = self._agents.get(intent, self._agents["data_analysis"])
        return agent.run(query, self.df, **agent_kwargs)

    # ── Intent classification ────────────────────────────────────

    def _classify_intent(self, query: str) -> str:
        for pattern, intent in INTENT_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return intent
        return "data_analysis"

    # ── Parameter extraction ─────────────────────────────────────

    def _extract_params(self, query: str, intent: str, **kwargs) -> Dict[str, Any]:
        params = dict(kwargs)

        # Extract Order_ID
        order_match = re.search(r"\bORD-\d+\b", query, re.IGNORECASE)
        if order_match:
            params["order_id"] = order_match.group(0).upper()

        # Extract date range
        date_match = re.findall(r"\d{4}-\d{2}-\d{2}", query)
        if len(date_match) >= 2:
            params["date_start"] = date_match[0]
            params["date_end"] = date_match[1]
        elif len(date_match) == 1:
            params["date_start"] = params["date_end"] = date_match[0]

        # Festive flag
        if re.search(r"\bfestive\b", query, re.IGNORECASE):
            params["festive_only"] = True

        # Shift filter
        for shift in ["Morning", "Evening", "Night"]:
            if shift.lower() in query.lower():
                params["shift"] = shift
                break

        # Zone filter
        for zone in ["Metro", "Tier-2", "Remote"]:
            if zone.lower() in query.lower():
                params["zone"] = zone
                break

        # Priority filter
        for pri in ["Express", "Standard", "Economy"]:
            if pri.lower() in query.lower():
                params["priority"] = pri
                break

        # Comparison flag
        if re.search(r"\bcompar(e|ison)\b", query, re.IGNORECASE):
            params["compare"] = True

        # Employee drill-down
        if re.search(r"\bemployee\b|\bpicker\b", query, re.IGNORECASE):
            params["include_employees"] = True

        return params

    # ── Convenience method ────────────────────────────────────────

    def available_agents(self) -> Dict[str, str]:
        return {
            "data_analysis":     "Warehouse Data Analysis Agent — KPIs, trends, summaries",
            "investigate_order": "Order Delay Investigation Agent — drill into a specific order",
            "bottleneck":        "Bottleneck Detection Agent — stage rankings, cause analysis",
            "shift":             "Shift Performance Analysis Agent — workload balance",
            "inventory":         "Inventory Shortage Analysis Agent — stock-out patterns",
            "recommendations":   "Operational Recommendation Agent — data-backed actions",
            "report":            "Automated Reporting Agent — full Markdown report",
        }
