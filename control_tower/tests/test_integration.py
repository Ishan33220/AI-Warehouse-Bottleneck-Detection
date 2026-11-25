"""
End-to-end integration tests for the FastAPI Web Interface (Phase 3 & 4).

Uses FastAPI's TestClient to verify:
  - HTML UI serving (GET /)
  - System status & agent listing (GET /api/status, GET /api/agents)
  - Chat endpoint routing across all 7 specialist agents (POST /api/chat)
  - Human-in-the-loop approval logging (POST /api/approve)
  - Validation errors on malformed payloads
"""

from fastapi.testclient import TestClient
from web.app import app, orchestrator

client = TestClient(app)


class TestWebEndpoints:
    def test_index_serves_html(self):
        res = client.get("/")
        assert res.status_code == 200
        assert "Warehouse Operations Control Tower" in res.text

    def test_status_endpoint(self):
        res = client.get("/api/status")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "online"
        assert data["dataset"]["rows"] == 2000
        assert data["dataset"]["delayed_orders"] == 328
        assert abs(data["dataset"]["on_time_delivery_pct"] - 83.1) < 0.2
        assert data["power_bi"]["preserved"] is True

    def test_agents_endpoint(self):
        res = client.get("/api/agents")
        assert res.status_code == 200
        agents = res.json()["agents"]
        assert len(agents) == 7
        for key in [
            "data_analysis",
            "investigate_order",
            "bottleneck",
            "shift",
            "inventory",
            "recommendations",
            "report",
        ]:
            assert key in agents

    def test_empty_query_rejected(self):
        res = client.post("/api/chat", json={"query": "   "})
        assert res.status_code == 400


class TestChatAllSevenAgents:
    def test_agent1_data_analysis(self):
        res = client.post("/api/chat", json={"query": "Show me the KPI overview"})
        assert res.status_code == 200
        data = res.json()
        assert data["agent"] == "Warehouse Data Analysis Agent"
        assert data["computed"]["total_orders"] == 2000

    def test_agent2_order_investigation(self):
        delayed_id = orchestrator.df[orchestrator.df["Delay_Status"] == "Delayed"]["Order_ID"].iloc[0]
        res = client.post("/api/chat", json={"query": f"Why was {delayed_id} delayed?"})
        assert res.status_code == 200
        data = res.json()
        assert data["agent"] == "Order Delay Investigation Agent"
        assert data["computed"]["found"] is True

    def test_agent3_bottleneck(self):
        res = client.post("/api/chat", json={"query": "What is the warehouse bottleneck?"})
        assert res.status_code == 200
        data = res.json()
        assert data["agent"] == "Bottleneck Detection Agent"
        assert data["computed"]["bottleneck"] == "Packing"
        assert len(data["chart_urls"]) >= 1
        assert data["chart_urls"][0].startswith("/outputs/")

    def test_agent4_shift(self):
        res = client.post("/api/chat", json={"query": "Which shift is busiest?"})
        assert res.status_code == 200
        data = res.json()
        assert data["agent"] == "Shift Performance Analysis Agent"
        assert data["computed"]["busiest_shift"] == "Evening"

    def test_agent5_inventory(self):
        res = client.post("/api/chat", json={"query": "What are the inventory shortage rates?"})
        assert res.status_code == 200
        data = res.json()
        assert data["agent"] == "Inventory Shortage Analysis Agent"
        assert "Electronics" in data["computed"]["at_risk_categories"]

    def test_agent6_recommendations_requires_approval(self):
        res = client.post("/api/chat", json={"query": "What are your recommendations to improve operations?"})
        assert res.status_code == 200
        data = res.json()
        assert data["agent"] == "Operational Recommendation Agent"
        assert data["requires_approval"] is True
        assert data["approval_item"]

    def test_agent7_report(self):
        res = client.post("/api/chat", json={"query": "Generate daily operations report"})
        assert res.status_code == 200
        data = res.json()
        assert data["agent"] == "Automated Reporting Agent"
        assert "saved_report" in data["computed"]
        assert "kpi_snapshot" in data["computed"]


class TestApprovalEndpoint:
    def test_approve_decision_logged(self):
        res = client.post(
            "/api/approve",
            json={
                "approval_item": "Reallocate 2 pickers to Evening shift Packing",
                "decision": "approved",
                "agent": "Operational Recommendation Agent",
                "notes": "Approved for festive surge test",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "recorded"
        assert data["record"]["decision"] == "approved"

    def test_reject_decision_logged(self):
        res = client.post(
            "/api/approve",
            json={
                "approval_item": "Increase safety stock by 20%",
                "decision": "rejected",
            },
        )
        assert res.status_code == 200
        assert res.json()["record"]["decision"] == "rejected"

    def test_invalid_decision_rejected(self):
        res = client.post(
            "/api/approve",
            json={
                "approval_item": "Test item",
                "decision": "maybe",
            },
        )
        assert res.status_code == 400
