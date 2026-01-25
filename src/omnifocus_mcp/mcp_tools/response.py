"""Response utilities for OmniFocus MCP tools.

This module provides helper functions for common response patterns,
including OmniJS JSON response handling and batch operation summaries.
"""

import json
from typing import Any

from ..omnijs import execute_omnijs_with_params


async def omnijs_json_response(
    script_name: str,
    params: dict[str, Any],
    includes: list[str] | None = None,
) -> str:
    """
    Execute an OmniJS script and return a JSON response.

    Wraps execute_omnijs_with_params with standard error handling,
    returning a JSON-formatted error message on exception.

    Args:
        script_name: Name of the script in scripts/ directory (without .js)
        params: Parameters to pass to the script
        includes: Optional list of scripts to include before the main script

    Returns:
        JSON string with the script result, or {"error": "..."} on failure
    """
    try:
        result = await execute_omnijs_with_params(script_name, params, includes=includes)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def build_batch_summary(
    results: list[dict[str, Any]],
    total: int | None = None,
) -> dict[str, Any]:
    """
    Build a standard batch operation summary.

    Args:
        results: List of individual operation results with 'success' boolean field
        total: Total number of items (defaults to len(results))

    Returns:
        Dictionary with standard batch summary structure:
        {
            "total": N,
            "success": M,
            "failed": N-M,
            "results": [...]
        }
    """
    success_count = sum(1 for r in results if r.get("success"))
    item_count = total if total is not None else len(results)
    failure_count = item_count - success_count

    return {
        "total": item_count,
        "success": success_count,
        "failed": failure_count,
        "results": results,
    }
