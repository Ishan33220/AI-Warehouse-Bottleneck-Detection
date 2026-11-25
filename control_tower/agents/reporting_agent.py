"""
Agent 7 – Automated Reporting Agent.

Assembles a full operational report from all agents, saves it as Markdown,
and optionally sends it via n8n webhook.
"""

import pandas as pd
from agents.base_agent import BaseAgent, AgentResponse
from tools.kpi_calculator import compute_all_kpis
from tools.report_generator import generate_markdown_report, save_report, save_kpi_snapshot
from tools.chart_generator import create_stage_delay_chart
from tools.bottleneck_detector import rank_stages_by_delays
from config.prompts import REPORT_SUMMARY_PROMPT
from datetime import datetime


class ReportingAgent(BaseAgent):
    """Generates structured operational reports from live data."""

    name = "Automated Reporting Agent"

    def run(self, query: str, df: pd.DataFrame, **kwargs) -> AgentResponse:
        """
        Optional kwargs:
            report_title : str  — custom title (default: 'Warehouse Operations Report')
            send_to_n8n  : bool — send via webhook (default False)
            save_charts  : bool — include charts in report (default True)
        """
        response = AgentResponse(self.name, query)
        title = kwargs.get("report_title", "Warehouse Operations Report")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        # ── Step 1: Compute all KPIs ─────────────────────────────
        kpi_data = compute_all_kpis(df)
        response.computed = {"kpi_data": kpi_data}

        # ── Step 2: Generate AI executive summary ─────────────────
        kpi_text = str(kpi_data.get("kpis", {}))[:800]
        bottleneck = kpi_data.get("top_delay_stage", "Packing")
        prompt = REPORT_SUMMARY_PROMPT.format(
            kpi_data=kpi_text,
            bottleneck=bottleneck,
        )
        exec_summary = self._ask_gemini(prompt)
        if not exec_summary:
            exec_summary = self._fallback_summary(kpi_data)

        # ── Step 3: Assemble report ───────────────────────────────
        report_md = generate_markdown_report(kpi_data, title)
        report_md = report_md.replace(
            "---",
            f"---\n\n## Executive Summary (AI Analysis)\n\n{exec_summary}\n\n---",
            1,
        )

        # ── Step 4: Save report and snapshot ─────────────────────
        filename = f"report_{ts}.md"
        saved_path = save_report(report_md, filename)
        kpi_path = save_kpi_snapshot(kpi_data, f"kpi_snapshot_{ts}.json")
        response.computed["saved_report"] = saved_path
        response.computed["kpi_snapshot"] = kpi_path

        response.ai_narrative = exec_summary

        # ── Step 5: Charts ────────────────────────────────────────
        if kwargs.get("save_charts", True):
            try:
                ranked = rank_stages_by_delays(df)
                chart = create_stage_delay_chart(ranked, f"delays_by_stage_{ts}.png")
                response.charts.append(chart)
            except Exception:
                pass

        # ── Step 6: n8n webhook ───────────────────────────────────
        if kwargs.get("send_to_n8n", False):
            self._send_to_n8n(kpi_data, saved_path)

        self._log(response)
        return response

    # ── Helpers ──────────────────────────────────────────────────

    def _fallback_summary(self, kpi_data: dict) -> str:
        kpis = kpi_data.get("kpis", {})
        bottleneck = kpi_data.get("top_delay_stage", "Packing")
        wh_delays = kpi_data.get("warehouse_controlled_delays", "N/A")
        return (
            f"The warehouse processed {kpis.get('total_orders', 'N/A'):,} orders with an "
            f"on-time delivery rate of {kpis.get('on_time_delivery_pct', 'N/A')}%. "
            f"The primary bottleneck is the {bottleneck} stage, which is responsible for "
            f"the largest share of warehouse-controlled delays. "
            f"A total of {wh_delays} delays are within the warehouse's direct control. "
            f"Priority action: address {bottleneck} stage capacity, particularly during peak "
            f"hours and festive periods."
        )

    def _send_to_n8n(self, kpi_data: dict, report_path: str) -> None:
        """POST a summary payload to the n8n webhook."""
        import os, urllib.request, json
        webhook_url = os.getenv("N8N_WEBHOOK_URL", "")
        if not webhook_url:
            return
        try:
            payload = json.dumps({
                "source": "warehouse_control_tower",
                "timestamp": datetime.now().isoformat(),
                "on_time_pct": kpi_data.get("kpis", {}).get("on_time_delivery_pct"),
                "delayed": kpi_data.get("kpis", {}).get("delayed_orders"),
                "bottleneck": kpi_data.get("top_delay_stage"),
                "report_path": report_path,
            }).encode()
            req = urllib.request.Request(
                webhook_url, data=payload,
                headers={"Content-Type": "application/json"}, method="POST"
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass  # Webhook failure is non-fatal
