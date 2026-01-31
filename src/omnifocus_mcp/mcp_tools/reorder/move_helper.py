"""Helper for moving tasks to a specific position or new parent."""

import json

from ..response import omnijs_json_response


async def move_task_to_parent(
    task_id: str,
    new_parent_id: str,
) -> tuple[bool, str]:
    """
    Move a task to a new parent (task or project).

    Args:
        task_id: ID of the task to move
        new_parent_id: ID of the new parent task or project.
            Use empty string to un-nest (move to project root).

    Returns:
        Tuple of (success: bool, message: str)
    """
    params = {
        "task_id": task_id,
        "new_parent_id": new_parent_id,
    }

    result_json = await omnijs_json_response("move_task_to_parent", params)
    result = json.loads(result_json)

    if result.get("error"):
        return False, result["error"]

    return result.get("success", False), result.get("message", "Unknown result")


async def move_task_to_position(
    task_id: str,
    position: str,
    reference_task_id: str | None = None,
) -> tuple[bool, str]:
    """
    Move a task to a specific position within its container.

    Args:
        task_id: ID of the task to move
        position: Target position - 'beginning', 'ending', 'before', 'after'
        reference_task_id: ID of reference task (required for 'before'/'after')

    Returns:
        Tuple of (success: bool, message: str)
    """
    params = {
        "task_id": task_id,
        "position": position,
    }
    if reference_task_id:
        params["reference_task_id"] = reference_task_id

    result_json = await omnijs_json_response("move_task", params)
    result = json.loads(result_json)

    if result.get("error"):
        return False, result["error"]

    return result.get("success", False), result.get("message", "Unknown result")
