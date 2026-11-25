"""
Tests for tools/data_loader.py.

Verifies that the dataset loads correctly, has the right shape, and that
convenience filters return the expected counts.
"""

import pytest
from tools.data_loader import (
    load_dataset, REQUIRED_COLUMNS,
    get_delivered, get_delayed, get_on_time,
    get_cancelled, get_in_transit,
    filter_festive, filter_non_festive,
    get_order_by_id,
)
from config.settings import DATASET_PATH


@pytest.fixture(scope="module")
def df():
    """Load the dataset once for the entire module."""
    return load_dataset(str(DATASET_PATH))


def test_row_count(df):
    assert len(df) == 2000, f"Expected 2000 rows, got {len(df)}"


def test_column_count(df):
    assert len(df.columns) == 24, f"Expected 24 columns, got {len(df.columns)}"


def test_all_required_columns_present(df):
    for col in REQUIRED_COLUMNS:
        assert col in df.columns, f"Missing column: {col}"


def test_delivered_count(df):
    assert len(get_delivered(df)) == 1941


def test_cancelled_count(df):
    assert len(get_cancelled(df)) == 52


def test_in_transit_count(df):
    assert len(get_in_transit(df)) == 7


def test_delayed_count(df):
    assert len(get_delayed(df)) == 328


def test_on_time_count(df):
    assert len(get_on_time(df)) == 1613


def test_status_sum(df):
    """Delivered + Cancelled + In Transit = 2000."""
    assert len(get_delivered(df)) + len(get_cancelled(df)) + len(get_in_transit(df)) == 2000


def test_delay_sum(df):
    """On Time + Delayed = Delivered."""
    assert len(get_on_time(df)) + len(get_delayed(df)) == len(get_delivered(df))


def test_no_negative_times(df):
    time_cols = [c for c in df.columns if c.endswith("_Minutes")]
    for col in time_cols:
        vals = df[col].dropna()
        assert (vals >= 0).all(), f"Negative values found in {col}"


def test_festive_non_festive_partition(df):
    """Festive + non-festive = all orders."""
    assert len(filter_festive(df)) + len(filter_non_festive(df)) == len(df)


def test_order_lookup(df):
    order = get_order_by_id(df, "ORD-100002")
    assert order is not None
    assert order["Customer_Location"] == "Lucknow"


def test_order_lookup_missing(df):
    assert get_order_by_id(df, "ORD-999999") is None


def test_caching():
    """Loading twice should return equal data (from cache)."""
    df1 = load_dataset(str(DATASET_PATH))
    df2 = load_dataset(str(DATASET_PATH))
    assert df1.equals(df2)
