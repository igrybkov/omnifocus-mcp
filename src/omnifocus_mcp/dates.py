"""Date utilities for OmniFocus AppleScript generation."""

from datetime import date, datetime
from typing import Any

import dateparser


def parse_natural_date(value: str) -> datetime | None:
    """
    Parse natural language date string to datetime.

    Supports:
    - "today", "tomorrow", "yesterday"
    - "this week", "last week", "next week"
    - "next monday", "last friday"
    - "in 3 days", "2 weeks ago"
    - ISO format: "2024-01-25"

    Args:
        value: Natural language date string or ISO format

    Returns:
        Parsed datetime, or None if unparseable
    """
    if not value or not isinstance(value, str):
        return None

    # Try ISO first (fast path)
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass

    # Use dateparser for natural language
    return dateparser.parse(
        value,
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.now(),
        },
    )


# Filters that expect N days from now
_DAYS_FILTERS = ("due_within", "deferred_until", "planned_within")


def preprocess_date_filters(filters: dict[str, Any]) -> dict[str, Any]:
    """
    Convert natural language dates to numeric days format.

    Processes filters like due_within, deferred_until, planned_within:
    - If string, parses natural language and converts to days from today
    - If already numeric, passes through unchanged

    Args:
        filters: Original filter dict

    Returns:
        New filter dict with date filters converted to numeric days
    """
    if not filters:
        return filters

    result = filters.copy()

    for key in _DAYS_FILTERS:
        if key in result and isinstance(result[key], str):
            parsed = parse_natural_date(result[key])
            if parsed:
                # Convert to days from today (can be negative for past dates)
                result[key] = (parsed.date() - date.today()).days
            else:
                # Unparseable - remove to avoid passing invalid value
                del result[key]

    return result


def parse_iso_date(iso_string: str) -> tuple[int, int, int, int, int, int]:
    """
    Parse an ISO date string to components.

    Args:
        iso_string: ISO format date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)

    Returns:
        Tuple of (year, month, day, hour, minute, second)
    """
    # Handle both date-only and datetime formats
    if "T" in iso_string:
        # Full ISO datetime
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    else:
        # Date only, default to midnight
        dt = datetime.fromisoformat(iso_string)

    return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


def create_date_applescript(iso_date: str, var_name: str) -> str:
    """
    Generate AppleScript code to create a date variable outside tell block.

    AppleScript doesn't allow date construction inside tell blocks,
    so dates must be created before the tell block and then assigned.

    Args:
        iso_date: ISO format date string
        var_name: Name of the AppleScript variable to create

    Returns:
        AppleScript code that creates the date variable
    """
    year, month, day, hour, minute, second = parse_iso_date(iso_date)

    return f"""copy current date to {var_name}
set year of {var_name} to {year}
set month of {var_name} to {month}
set day of {var_name} to {day}
set hours of {var_name} to {hour}
set minutes of {var_name} to {minute}
set seconds of {var_name} to {second}"""


def create_date_assignment(
    iso_date: str | None, property_name: str, object_var: str, date_var_prefix: str = "dateVar"
) -> tuple[str, str]:
    """
    Generate AppleScript code for date handling with pre-tell and in-tell parts.

    Args:
        iso_date: ISO format date string, empty string to clear, or None to skip
        property_name: Name of the property to set (e.g., "due date", "defer date")
        object_var: Name of the AppleScript variable for the object being modified
        date_var_prefix: Prefix for the date variable name

    Returns:
        Tuple of (pre_tell_script, in_tell_assignment)
        - pre_tell_script: Code to run before tell block (date creation)
        - in_tell_assignment: Code to run inside tell block (assignment)
    """
    if iso_date is None:
        return ("", "")

    if iso_date == "":
        # Clear the date
        return ("", f"set {property_name} of {object_var} to missing value")

    # Create unique variable name
    import random
    import string

    suffix = "".join(random.choices(string.ascii_lowercase, k=8))
    var_name = f"{date_var_prefix}_{suffix}"

    pre_script = create_date_applescript(iso_date, var_name)
    assignment = f"set {property_name} of {object_var} to {var_name}"

    return (pre_script, assignment)
