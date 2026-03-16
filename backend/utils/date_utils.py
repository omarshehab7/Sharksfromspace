"""
date_utils.py — Date & Time Utility Functions
================================================

Helper functions for working with date ranges
and temporal queries for satellite data.
"""

from datetime import datetime, timedelta


def get_date_range(days_back: int = 7) -> str:
    """
    Generate an ISO 8601 date range string for NASA data queries.

    Args:
        days_back: Number of days to look back from today

    Returns:
        Comma-separated date range string (e.g., "2024-01-01,2024-01-07")
    """
    end = datetime.utcnow()
    start = end - timedelta(days=days_back)
    return f"{start.strftime('%Y-%m-%d')},{end.strftime('%Y-%m-%d')}"


def parse_iso_datetime(iso_string: str) -> datetime:
    """
    Parse an ISO 8601 datetime string.

    Args:
        iso_string: ISO format datetime (e.g., "2024-01-15T12:00:00Z")

    Returns:
        datetime object
    """
    # Handle various ISO formats
    for fmt in [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]:
        try:
            return datetime.strptime(iso_string, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {iso_string}")


def get_season(date: datetime) -> str:
    """
    Determine the meteorological season for a date.

    Returns:
        Season name (spring, summer, fall, winter)
    """
    month = date.month
    if month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    elif month in (9, 10, 11):
        return "fall"
    return "winter"
