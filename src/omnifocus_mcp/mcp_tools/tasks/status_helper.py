"""Helper for changing task status via OmniJS.

Uses OmniJS instead of AppleScript to handle all task types
including inbox tasks, which don't support AppleScript property setters.
"""

import json

from ..response import omnijs_json_response


async def change_task_status(
    task_id: str,
    status: str,
) -> tuple[bool, str]:
    """
    Change a task's status via OmniJS.

    Works for all task types including inbox tasks.

    Args:
        task_id: ID of the task to modify
        status: Target status - 'completed', 'dropped', or 'incomplete'

    Returns:
        Tuple of (success: bool, message: str)
    """
    params = {
        "task_id": task_id,
        "status": status,
    }

    result_json = await omnijs_json_response("change_task_status", params)
    result = json.loads(result_json)

    if result.get("error"):
        return False, result["error"]

    return result.get("success", False), result.get("message", "Unknown result")
