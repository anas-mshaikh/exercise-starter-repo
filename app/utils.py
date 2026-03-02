"""
Shared utilities.

All timestamp handling should use the functions in this module
to ensure consistent UTC normalization across the application.
"""

from datetime import datetime, timezone


def now_utc() -> str:
    """Return the current time as an ISO 8601 string in UTC."""
    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(value: str) -> datetime:
    """
    Parse an ISO 8601 timestamp string and normalize to UTC.
    
    Handles both timezone-aware and naive timestamps.
    Naive timestamps are assumed to be UTC.
    
    Raises ValueError if the string is not a valid ISO 8601 timestamp.
    """
    try:
        dt = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid ISO 8601 timestamp: {value}")

    # Normalize to UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt


def format_timestamp(dt: datetime) -> str:
    """Format a datetime object as an ISO 8601 string in UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


VALID_CATEGORIES = {"page_view", "click", "form_submit", "purchase", "error"}


def validate_category(category: str) -> str:
    """
    Validate that a category is one of the allowed values.
    
    Returns the category if valid, raises ValueError if not.
    """
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category '{category}'. "
            f"Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
        )
    return category
