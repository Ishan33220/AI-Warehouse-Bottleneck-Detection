"""
Tests for tools/kpi_calculator.py.

Validates every computed KPI against the reference values in kpi_summary.json.
Uses pytest.approx with abs=0.15 tolerance to handle rounding differences.
"""

import pytest
import json
from tools.data_loader import load_dataset
from tools.kpi_calculator import (
    compute_core_kpis, compute_stage_metrics, compute_delay_split,
    compute_top_delay_reasons, compute_festive_comparison,
    compute_shortage_by_category, compute_delayed_by_priority,
    compute_delayed_by_zone,
)
from config.settings import DATASET_PATH, KPI_REFERENCE_PATH


@pytest.fixture(scope="module")
def df():
    return load_dataset(str(DATASET_PATH))


@pytest.fixture(scope="module")
def reference():
    with open(KPI_REFERENCE_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── Core KPIs ────────────────────────────────────────────────────

class TestCoreKPIs:
    def test_total_orders(self, df, reference):
        kpis = compute_core_kpis(df)
        assert kpis["total_orders"] == reference["kpis"]["total_orders"]

    def test_delivered(self, df, reference):
        kpis = compute_core_kpis(df)
        assert kpis["completed_orders_delivered"] == reference["kpis"]["completed_orders_delivered"]

    def test_cancelled(self, df, reference):
        kpis = compute_core_kpis(df)
        assert kpis["cancelled_orders"] == reference["kpis"]["cancelled_orders"]

    def test_in_transit(self, df, reference):
        kpis = compute_core_kpis(df)
        assert kpis["in_transit_orders"] == reference["kpis"]["in_transit_orders"]

    def test_delayed(self, df, reference):
        kpis = compute_core_kpis(df)
        assert kpis["delayed_orders"] == reference["kpis"]["delayed_orders"]

    def test_on_time_pct(self, df, reference):
        kpis = compute_core_kpis(df)
        assert kpis["on_time_delivery_pct"] == pytest.approx(
            reference["kpis"]["on_time_delivery_pct"], abs=0.15
        )

    def test_avg_picking(self, df, reference):
        kpis = compute_core_kpis(df)
        assert kpis["avg_picking_minutes"] == pytest.approx(
            reference["kpis"]["avg_picking_minutes"], abs=0.15
        )

    def test_avg_packing(self, df, reference):
        kpis = compute_core_kpis(df)
        assert kpis["avg_packing_minutes"] == pytest.approx(
            reference["kpis"]["avg_packing_minutes"], abs=0.15
        )

    def test_avg_delivery_hours(self, df, reference):
        kpis = compute_core_kpis(df)
        assert kpis["avg_delivery_hours"] == pytest.approx(
            reference["kpis"]["avg_delivery_hours"], abs=0.15
        )

    def test_shortage_pct(self, df, reference):
        kpis = compute_core_kpis(df)
        assert kpis["inventory_shortage_pct"] == pytest.approx(
            reference["kpis"]["inventory_shortage_pct"], abs=0.15
        )

    def test_total_cost(self, df, reference):
        kpis = compute_core_kpis(df)
        assert kpis["total_operational_cost_rs"] == pytest.approx(
            reference["kpis"]["total_operational_cost_rs"], abs=1.0
        )


# ── Stage metrics ────────────────────────────────────────────────

class TestStageMetrics:
    def test_all_six_stages_present(self, df):
        stages = compute_stage_metrics(df)
        names = {s["stage"] for s in stages}
        assert names == {"Receiving", "Inventory", "Picking", "Packing", "Dispatch", "Delivery"}

    def test_delay_counts_match(self, df, reference):
        stages = compute_stage_metrics(df)
        ref_map = {s["stage"]: s for s in reference["stages"]}
        for s in stages:
            assert s["delays_caused"] == ref_map[s["stage"]]["delays_caused"], (
                f"{s['stage']}: expected {ref_map[s['stage']]['delays_caused']}, "
                f"got {s['delays_caused']}"
            )

    def test_avg_minutes_match(self, df, reference):
        stages = compute_stage_metrics(df)
        ref_map = {s["stage"]: s for s in reference["stages"]}
        for s in stages:
            assert s["avg_minutes"] == pytest.approx(
                ref_map[s["stage"]]["avg_minutes"], abs=0.15
            ), f"{s['stage']} avg mismatch"

    def test_share_of_delays_match(self, df, reference):
        stages = compute_stage_metrics(df)
        ref_map = {s["stage"]: s for s in reference["stages"]}
        for s in stages:
            assert s["share_of_delays_pct"] == pytest.approx(
                ref_map[s["stage"]]["share_of_delays_pct"], abs=0.15
            )


# ── Delay split ──────────────────────────────────────────────────

class TestDelaySplit:
    def test_warehouse_delays(self, df, reference):
        split = compute_delay_split(df)
        assert split["warehouse_controlled_delays"] == reference["warehouse_controlled_delays"]

    def test_courier_delays(self, df, reference):
        split = compute_delay_split(df)
        assert split["courier_delays"] == reference["courier_delays"]

    def test_sum_equals_total_delayed(self, df):
        split = compute_delay_split(df)
        assert split["warehouse_controlled_delays"] + split["courier_delays"] == 328


# ── Delay reasons ────────────────────────────────────────────────

class TestDelayReasons:
    def test_top_reasons_match(self, df, reference):
        reasons = compute_top_delay_reasons(df)
        ref_reasons = reference["top_delay_reasons"]
        for reason, expected_count in ref_reasons.items():
            assert reasons.get(reason) == expected_count, (
                f"Reason '{reason}': expected {expected_count}, got {reasons.get(reason)}"
            )


# ── Festive comparison ───────────────────────────────────────────

class TestFestiveComparison:
    def test_festive_orders_per_day(self, df, reference):
        result = compute_festive_comparison(df)
        ref = reference["festive_week_vs_other_days"]
        assert result["festive_orders_per_day"] == pytest.approx(
            ref["festive_orders_per_day"], abs=0.15
        )

    def test_festive_delayed_pct(self, df, reference):
        result = compute_festive_comparison(df)
        ref = reference["festive_week_vs_other_days"]
        assert result["festive_delayed_pct"] == pytest.approx(
            ref["festive_delayed_pct"], abs=0.15
        )


# ── Dimension breakdowns ────────────────────────────────────────

class TestDimensionBreakdowns:
    def test_shortage_by_category(self, df, reference):
        result = compute_shortage_by_category(df)
        for cat, pct in reference["shortage_pct_by_category"].items():
            assert result[cat] == pytest.approx(pct, abs=0.15), f"{cat} shortage mismatch"

    def test_delayed_by_priority(self, df, reference):
        result = compute_delayed_by_priority(df)
        for pri, pct in reference["delayed_pct_by_priority"].items():
            assert result[pri] == pytest.approx(pct, abs=0.15), f"{pri} delay mismatch"

    def test_delayed_by_zone(self, df, reference):
        result = compute_delayed_by_zone(df)
        for zone, pct in reference["delayed_pct_by_zone"].items():
            assert result[zone] == pytest.approx(pct, abs=0.15), f"{zone} delay mismatch"
