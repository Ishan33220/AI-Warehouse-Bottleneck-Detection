"""
Integration tests for the Agent layer (Phase 2).

Tests that agents load data, call tools, return valid AgentResponse objects,
and produce correct computed data — WITHOUT requiring a Gemini API key.
(The AI narrative falls back to a plain-text string when no key is present.)
"""

import pytest
import os
from agents.orchestrator import Orchestrator
from agents.base_agent import AgentResponse


@pytest.fixture(scope="module")
def orch():
    """Shared orchestrator with data loaded once."""
    o = Orchestrator()
    o.load_data()
    return o


# ── Orchestrator intent routing ──────────────────────────────────

class TestOrchestratorRouting:
    def test_classify_bottleneck(self, orch):
        assert orch._classify_intent("What is the bottleneck?") == "bottleneck"

    def test_classify_shift(self, orch):
        assert orch._classify_intent("How is the Evening shift performing?") == "shift"

    def test_classify_inventory(self, orch):
        assert orch._classify_intent("What is the inventory shortage rate?") == "inventory"

    def test_classify_investigate(self, orch):
        assert orch._classify_intent("Why was ORD-100547 delayed?") == "investigate_order"

    def test_classify_report(self, orch):
        assert orch._classify_intent("Generate a report") == "report"

    def test_classify_recommendations(self, orch):
        assert orch._classify_intent("What are your recommendations?") == "recommendations"

    def test_classify_data_default(self, orch):
        assert orch._classify_intent("Show me KPI summary") == "data_analysis"

    def test_extract_order_id(self, orch):
        params = orch._extract_params("Why was ORD-100042 late?", "investigate_order")
        assert params["order_id"] == "ORD-100042"

    def test_extract_shift(self, orch):
        params = orch._extract_params("How is the Morning shift doing?", "shift")
        assert params.get("shift") == "Morning"

    def test_extract_zone(self, orch):
        params = orch._extract_params("Show Remote zone performance", "data_analysis")
        assert params.get("zone") == "Remote"


# ── Agent 1: Data Analysis ────────────────────────────────────────

class TestDataAnalysisAgent:
    def test_returns_agent_response(self, orch):
        resp = orch.dispatch("Show me the KPI overview")
        assert isinstance(resp, AgentResponse)

    def test_total_orders_correct(self, orch):
        resp = orch.dispatch("How many total orders?")
        assert resp.computed.get("total_orders") == 2000

    def test_delayed_correct(self, orch):
        resp = orch.dispatch("How many orders were delayed?")
        assert resp.computed.get("delayed_orders") == 328

    def test_on_time_pct_correct(self, orch):
        resp = orch.dispatch("What is the on-time delivery percentage?")
        assert abs(resp.computed.get("on_time_delivery_pct", 0) - 83.1) < 0.2

    def test_shift_filter(self, orch):
        resp = orch.dispatch("Show stats for the Morning shift")
        assert resp.computed.get("total_orders", 0) < 2000  # filtered

    def test_no_error(self, orch):
        resp = orch.dispatch("Give me an overview")
        assert resp.error is None


# ── Agent 2: Order Investigation ─────────────────────────────────

class TestDelayInvestigationAgent:
    def test_known_delayed_order(self, orch):
        # Find a delayed order to test
        delayed = orch.df[orch.df["Delay_Status"] == "Delayed"]["Order_ID"].iloc[0]
        resp = orch.dispatch(f"Why was {delayed} delayed?")
        assert resp.error is None
        assert resp.computed.get("found") is True
        assert resp.computed.get("delay_status") == "Delayed"

    def test_missing_order(self, orch):
        resp = orch.dispatch("Why was ORD-999999 delayed?")
        assert resp.error is not None

    def test_stage_analysis_present(self, orch):
        delayed = orch.df[orch.df["Delay_Status"] == "Delayed"]["Order_ID"].iloc[0]
        resp = orch.dispatch(f"Investigate {delayed}")
        assert "stage_analysis" in resp.computed

    def test_contextual_factors_present(self, orch):
        delayed = orch.df[orch.df["Delay_Status"] == "Delayed"]["Order_ID"].iloc[0]
        resp = orch.dispatch(f"Investigate {delayed}")
        assert "contextual_factors" in resp.computed

    def test_no_order_id_error(self, orch):
        resp = orch.dispatch("investigate an order")
        assert resp.error is not None


# ── Agent 3: Bottleneck ───────────────────────────────────────────

class TestBottleneckAgent:
    def test_packing_bottleneck(self, orch):
        resp = orch.dispatch("What is the warehouse bottleneck?")
        assert resp.computed.get("bottleneck") == "Packing"

    def test_bottleneck_delays(self, orch):
        resp = orch.dispatch("What is the bottleneck?")
        assert resp.computed.get("bottleneck_delays") == 123

    def test_stage_ranking_present(self, orch):
        resp = orch.dispatch("Which stage causes the most delays?")
        assert "stage_ranking" in resp.computed
        assert len(resp.computed["stage_ranking"]) == 6

    def test_warehouse_share(self, orch):
        resp = orch.dispatch("What share of delays are warehouse-controlled?")
        share = resp.computed.get("warehouse_delay_share", {})
        assert share.get("warehouse_share_pct", 0) == pytest.approx(75.0, abs=0.2)


# ── Agent 4: Shift Performance ────────────────────────────────────

class TestShiftPerformanceAgent:
    def test_busiest_shift(self, orch):
        resp = orch.dispatch("Which shift is busiest?")
        assert resp.computed.get("busiest_shift") == "Evening"

    def test_imbalance_ratio(self, orch):
        resp = orch.dispatch("Show workload balance across shifts")
        assert resp.computed.get("workload_imbalance_ratio", 1) > 1

    def test_shift_metrics_present(self, orch):
        resp = orch.dispatch("Compare Morning and Evening shifts")
        metrics = resp.computed.get("shift_metrics", [])
        assert len(metrics) == 3


# ── Agent 5: Inventory ────────────────────────────────────────────

class TestInventoryAgent:
    def test_electronics_at_risk(self, orch):
        resp = orch.dispatch("What are the inventory shortage rates?")
        at_risk = resp.computed.get("at_risk_categories", [])
        assert "Electronics" in at_risk

    def test_inventory_summary(self, orch):
        resp = orch.dispatch("Show me inventory status")
        summary = resp.computed.get("inventory_summary", {})
        assert summary.get("total_orders") == 2000

    def test_impact_data(self, orch):
        resp = orch.dispatch("How many cancellations were due to stock-outs?")
        impact = resp.computed.get("operational_impact", {})
        assert impact.get("inventory_stage_delays") == 64


# ── Agent 6: Recommendations ──────────────────────────────────────

class TestRecommendationAgent:
    def test_produces_response(self, orch):
        resp = orch.dispatch("What are your recommendations to improve operations?")
        assert isinstance(resp, AgentResponse)
        assert resp.error is None

    def test_supporting_evidence(self, orch):
        resp = orch.dispatch("Give me recommendations")
        evidence = resp.computed.get("supporting_evidence", {})
        assert "bottleneck" in evidence
        assert "shift" in evidence
        assert "inventory" in evidence

    def test_has_narrative(self, orch):
        resp = orch.dispatch("What should we improve first?")
        assert len(resp.ai_narrative) > 50


# ── Agent 7: Reporting ────────────────────────────────────────────

class TestReportingAgent:
    def test_report_saved(self, orch):
        resp = orch.dispatch("Generate a report", save_charts=False)
        assert resp.computed.get("saved_report") is not None
        import os
        assert os.path.exists(resp.computed["saved_report"])

    def test_kpi_snapshot_saved(self, orch):
        resp = orch.dispatch("Generate report", save_charts=False)
        assert resp.computed.get("kpi_snapshot") is not None
        import os
        assert os.path.exists(resp.computed["kpi_snapshot"])

    def test_report_contains_key_numbers(self, orch):
        resp = orch.dispatch("Summary report", save_charts=False)
        path = resp.computed.get("saved_report")
        if path:
            content = open(path, encoding="utf-8").read()
            assert "2,000" in content or "2000" in content
            assert "83.1" in content


# ── to_text output ───────────────────────────────────────────────

class TestAgentResponseText:
    def test_computed_label_in_text(self, orch):
        resp = orch.dispatch("KPI overview")
        text = resp.to_text()
        assert "🟢 [COMPUTED]" in text

    def test_approval_flag(self, orch):
        resp = orch.dispatch("What are your recommendations?")
        # Approval may or may not trigger depending on AI content;
        # test that the field exists and is bool
        assert isinstance(resp.requires_approval, bool)
