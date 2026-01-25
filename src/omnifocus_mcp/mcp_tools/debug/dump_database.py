"""Database dump tool for OmniFocus."""

import json

from ...omnijs import execute_omnijs_with_params


async def dump_database(
    hide_completed: bool = True,
    hide_recurring_duplicates: bool = True,
) -> str:
    """
    Gets the complete current state of your OmniFocus database in a compact, formatted report.

    NOTE: This tool is only available when running with --expanded flag.

    Args:
        hide_completed: Set to False to show completed and dropped tasks (default: True)
        hide_recurring_duplicates: Set to True to hide duplicate instances of
            recurring tasks (default: True)

    Returns:
        Formatted database dump with hierarchical structure
    """
    try:
        result = await execute_omnijs_with_params(
            "dump_database",
            {
                "hide_completed": hide_completed,
                "hide_recurring_duplicates": hide_recurring_duplicates,
            },
        )
        # The result might be wrapped in quotes from JSON, handle both cases
        if isinstance(result, dict):
            if "error" in result:
                return f"Error: {result['error']}"
            if "result" in result:
                return result["result"]
            return json.dumps(result, indent=2)
        return str(result)
    except Exception as e:
        return f"Error dumping database: {str(e)}"
