"""
Load and validate the warehouse orders dataset.

This is the single entry-point for all data access. It loads the CSV once,
validates the schema, and caches the DataFrame in memory so every tool
works from the same snapshot.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ── Module-level cache ───────────────────────────────────────────
_cached_df: Optional[pd.DataFrame] = None
_cached_path: Optional[str] = None

# ── Required columns (all 24) ───────────────────────────────────
REQUIRED_COLUMNS = [
    "Order_ID", "Order_Date", "Order_Hour", "Shift",
    "Customer_Location", "Delivery_Zone", "Product_Category",
    "Order_Priority", "Order_Quantity", "Inventory_Status",
    "Receiving_Time_Minutes", "Inventory_Check_Time_Minutes",
    "Picking_Time_Minutes", "Packing_Time_Minutes",
    "Dispatch_Time_Minutes", "Delivery_Time_Minutes",
    "Total_Time_Minutes", "SLA_Minutes", "Order_Status",
    "Delay_Status", "Delay_Stage", "Delay_Reason",
    "Warehouse_Employee_ID", "Operational_Cost",
]


def load_dataset(path: Optional[str] = None, force_reload: bool = False) -> pd.DataFrame:
    """
    Load the clean warehouse orders CSV.

    Parameters
    ----------
    path : str, optional
        Override path to the CSV. Defaults to config.settings.DATASET_PATH.
    force_reload : bool
        If True, bypass the cache and reload from disk.

    Returns
    -------
    pd.DataFrame
        A fresh copy of the validated dataset (2,000 rows, 24 columns).
    """
    global _cached_df, _cached_path

    if path is None:
        from config.settings import DATASET_PATH
        path = str(DATASET_PATH)

    # Return cached copy if available
    if not force_reload and _cached_df is not None and _cached_path == path:
        return _cached_df.copy()

    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path, parse_dates=["Order_Date"])

    # Validate required columns
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    logger.info("Loaded %d orders from %s", len(df), path)

    # Cache it
    _cached_df = df
    _cached_path = path
    return df.copy()


# ═══════════════════════════════════════════════════════════════════
# Convenience filters (always return a copy)
# ═══════════════════════════════════════════════════════════════════

def get_delivered(df: pd.DataFrame) -> pd.DataFrame:
    """Return only delivered orders."""
    return df[df["Order_Status"] == "Delivered"].copy()


def get_delayed(df: pd.DataFrame) -> pd.DataFrame:
    """Return only delayed orders (subset of delivered)."""
    return df[df["Delay_Status"] == "Delayed"].copy()


def get_on_time(df: pd.DataFrame) -> pd.DataFrame:
    """Return only on-time orders (subset of delivered)."""
    return df[df["Delay_Status"] == "On Time"].copy()


def get_cancelled(df: pd.DataFrame) -> pd.DataFrame:
    """Return only cancelled orders."""
    return df[df["Order_Status"] == "Cancelled"].copy()


def get_in_transit(df: pd.DataFrame) -> pd.DataFrame:
    """Return only in-transit orders."""
    return df[df["Order_Status"] == "In Transit"].copy()


def filter_by_date_range(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Filter orders by date range (inclusive)."""
    mask = (df["Order_Date"] >= pd.Timestamp(start)) & (df["Order_Date"] <= pd.Timestamp(end))
    return df[mask].copy()


def filter_by_shift(df: pd.DataFrame, shift: str) -> pd.DataFrame:
    """Filter by shift name (Morning / Evening / Night)."""
    return df[df["Shift"] == shift].copy()


def filter_by_zone(df: pd.DataFrame, zone: str) -> pd.DataFrame:
    """Filter by delivery zone (Metro / Tier-2 / Remote)."""
    return df[df["Delivery_Zone"] == zone].copy()


def filter_by_category(df: pd.DataFrame, category: str) -> pd.DataFrame:
    """Filter by product category."""
    return df[df["Product_Category"] == category].copy()


def filter_by_priority(df: pd.DataFrame, priority: str) -> pd.DataFrame:
    """Filter by order priority (Express / Standard / Economy)."""
    return df[df["Order_Priority"] == priority].copy()


def filter_festive(df: pd.DataFrame) -> pd.DataFrame:
    """Return orders during the festive week (15–21 Oct 2026)."""
    from config.settings import FESTIVE_START, FESTIVE_END
    return filter_by_date_range(df, FESTIVE_START, FESTIVE_END)


def filter_non_festive(df: pd.DataFrame) -> pd.DataFrame:
    """Return orders outside the festive week."""
    from config.settings import FESTIVE_START, FESTIVE_END
    start = pd.Timestamp(FESTIVE_START)
    end = pd.Timestamp(FESTIVE_END)
    mask = (df["Order_Date"] < start) | (df["Order_Date"] > end)
    return df[mask].copy()


def get_order_by_id(df: pd.DataFrame, order_id: str) -> Optional[pd.Series]:
    """Look up a single order by Order_ID. Returns None if not found."""
    matches = df[df["Order_ID"] == order_id]
    if len(matches) == 0:
        return None
    return matches.iloc[0]
