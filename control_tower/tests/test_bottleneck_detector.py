"""
Tests for tools/bottleneck_detector.py.

Verifies bottleneck detection, stage ranking, and cause analysis.
"""

import pytest
from tools.data_loader import load_dataset, filter_festive, filter_non_festive
from tools.bottleneck_detector import (
    detect_bottleneck, compute_warehouse_delay_share,
    rank_stages_by_delays, analyze_bottleneck_causes,
    compare_bottlenecks,
)
from config.settings import DATASET_PATH


@pytest.fixture(scope="module")
def df():
    return load_dataset(str(DATASET_PATH))


class TestDetectBottleneck:
    def test_warehouse_bottleneck_is_packing(self, df):
        result = detect_bottleneck(df, scope="warehouse")
        assert result["bottleneck"] == "Packing"

    def test_bottleneck_delay_count(self, df):
        result = detect_bottleneck(df, scope="warehouse")
        assert result["bottleneck_delays"] == 123

    def test_bottleneck_share(self, df):
        result = detect_bottleneck(df, scope="warehouse")
        assert result["bottleneck_share_pct"] == pytest.approx(37.5, abs=0.15)

    def test_total_delayed(self, df):
        result = detect_bottleneck(df)
        assert result["total_delayed"] == 328

    def test_all_scope_includes_delivery(self, df):
        result = detect_bottleneck(df, scope="all")
        assert "Delivery" in result["stage_delays"]


class TestWarehouseDelayShare:
    def test_warehouse_delays_count(self, df):
        result = compute_warehouse_delay_share(df)
        assert result["warehouse_delays"] == 246

    def test_courier_delays_count(self, df):
        result = compute_warehouse_delay_share(df)
        assert result["courier_delays"] == 82

    def test_warehouse_share_pct(self, df):
        result = compute_warehouse_delay_share(df)
        assert result["warehouse_share_pct"] == pytest.approx(75.0, abs=0.15)


class TestStageRanking:
    def test_packing_ranks_first(self, df):
        ranked = rank_stages_by_delays(df)
        assert ranked[0]["stage"] == "Packing"
        assert ranked[0]["delays_caused"] == 123

    def test_all_six_stages_ranked(self, df):
        ranked = rank_stages_by_delays(df)
        assert len(ranked) == 6

    def test_descending_order(self, df):
        ranked = rank_stages_by_delays(df)
        for i in range(len(ranked) - 1):
            assert ranked[i]["delays_caused"] >= ranked[i + 1]["delays_caused"]


class TestBottleneckCauses:
    def test_packing_causes(self, df):
        result = analyze_bottleneck_causes(df, "Packing")
        assert result["total_delays_at_stage"] == 123
        assert "Packing station congestion (peak load)" in result["reasons"]

    def test_auto_detect_stage(self, df):
        result = analyze_bottleneck_causes(df)
        assert result["stage"] == "Packing"

    def test_inventory_causes(self, df):
        result = analyze_bottleneck_causes(df, "Inventory")
        assert result["total_delays_at_stage"] == 64
        assert "Stock-out - awaiting replenishment" in result["reasons"]


class TestCompareBottlenecks:
    def test_festive_vs_normal(self, df):
        festive = filter_festive(df)
        normal = filter_non_festive(df)
        result = compare_bottlenecks(df, "Festive", festive, "Normal", normal)
        assert "Festive" in result
        assert "Normal" in result
        assert isinstance(result["same_bottleneck"], bool)
