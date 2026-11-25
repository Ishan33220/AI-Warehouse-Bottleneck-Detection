"""
Tests for tools/shift_analyzer.py and tools/inventory_analyzer.py.
"""

import pytest
import json
from tools.data_loader import load_dataset
from tools.shift_analyzer import compute_shift_metrics, compare_shifts, analyze_employee_performance
from tools.inventory_analyzer import (
    compute_inventory_summary, compute_shortage_by_category,
    compute_shortage_impact, identify_at_risk_categories,
)
from config.settings import DATASET_PATH, KPI_REFERENCE_PATH


@pytest.fixture(scope="module")
def df():
    return load_dataset(str(DATASET_PATH))


@pytest.fixture(scope="module")
def reference():
    with open(KPI_REFERENCE_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── Shift Analyzer ───────────────────────────────────────────────

class TestShiftMetrics:
    def test_three_shifts(self, df):
        metrics = compute_shift_metrics(df)
        assert len(metrics) == 3

    def test_shift_order_counts(self, df, reference):
        metrics = {m["shift"]: m for m in compute_shift_metrics(df)}
        ref_map = {s["shift"]: s for s in reference["shifts"]}
        for shift in ["Morning", "Evening", "Night"]:
            assert metrics[shift]["orders"] == ref_map[shift]["orders"]

    def test_shift_employee_counts(self, df, reference):
        metrics = {m["shift"]: m for m in compute_shift_metrics(df)}
        ref_map = {s["shift"]: s for s in reference["shifts"]}
        for shift in ["Morning", "Evening", "Night"]:
            assert metrics[shift]["employees"] == ref_map[shift]["employees"]

    def test_shift_avg_picking(self, df, reference):
        metrics = {m["shift"]: m for m in compute_shift_metrics(df)}
        ref_map = {s["shift"]: s for s in reference["shifts"]}
        for shift in ["Morning", "Evening", "Night"]:
            assert metrics[shift]["avg_picking_minutes"] == pytest.approx(
                ref_map[shift]["avg_picking_minutes"], abs=0.15
            )

    def test_shift_delayed_pct(self, df, reference):
        metrics = {m["shift"]: m for m in compute_shift_metrics(df)}
        ref_map = {s["shift"]: s for s in reference["shifts"]}
        for shift in ["Morning", "Evening", "Night"]:
            assert metrics[shift]["delayed_pct"] == pytest.approx(
                ref_map[shift]["delayed_pct"], abs=0.15
            )


class TestShiftComparison:
    def test_busiest_is_evening(self, df):
        result = compare_shifts(df)
        assert result["busiest_shift"] == "Evening"

    def test_workload_imbalance(self, df):
        result = compare_shifts(df)
        assert result["workload_imbalance_ratio"] > 1.0


class TestEmployeePerformance:
    def test_twenty_employees(self, df):
        employees = analyze_employee_performance(df)
        assert len(employees) == 20

    def test_trainees_flagged(self, df):
        employees = analyze_employee_performance(df)
        trainees = [e for e in employees if e["is_trainee"]]
        assert len(trainees) == 3
        trainee_ids = {e["employee_id"] for e in trainees}
        assert trainee_ids == {"EMP005", "EMP012", "EMP018"}


# ── Inventory Analyzer ───────────────────────────────────────────

class TestInventorySummary:
    def test_status_counts(self, df):
        summary = compute_inventory_summary(df)
        assert summary["total_orders"] == 2000
        assert summary["available"] + summary["low_stock"] + summary["out_of_stock"] == 2000

    def test_shortage_pct(self, df, reference):
        summary = compute_inventory_summary(df)
        assert summary["shortage_pct"] == pytest.approx(
            reference["kpis"]["inventory_shortage_pct"], abs=0.15
        )


class TestShortageByCategory:
    def test_matches_reference(self, df, reference):
        result = compute_shortage_by_category(df)
        for cat, pct in reference["shortage_pct_by_category"].items():
            assert result[cat] == pytest.approx(pct, abs=0.15), f"{cat} mismatch"

    def test_electronics_highest(self, df):
        result = compute_shortage_by_category(df)
        cats = list(result.keys())
        assert cats[0] == "Electronics"


class TestShortageImpact:
    def test_oos_cancellations(self, df):
        result = compute_shortage_impact(df)
        assert result["oos_cancellations"] > 0
        assert result["oos_cancellations"] <= result["total_cancellations"]

    def test_inventory_delays(self, df):
        result = compute_shortage_impact(df)
        assert result["inventory_stage_delays"] == 64

    def test_oos_wait_longer(self, df):
        result = compute_shortage_impact(df)
        assert result["avg_inventory_time_oos"] > result["avg_inventory_time_available"]


class TestAtRiskCategories:
    def test_electronics_at_risk(self, df):
        at_risk = identify_at_risk_categories(df, threshold_pct=10.0)
        assert "Electronics" in at_risk

    def test_books_not_at_risk(self, df):
        at_risk = identify_at_risk_categories(df, threshold_pct=10.0)
        assert "Books & Stationery" not in at_risk

    def test_combined_shortage_expands_at_risk(self, df):
        oos_risk = identify_at_risk_categories(df, threshold_pct=10.0, oos_only=True)
        combined_risk = identify_at_risk_categories(df, threshold_pct=10.0, oos_only=False)
        assert len(combined_risk) > len(oos_risk)
        assert "Fashion & Apparel" in combined_risk
