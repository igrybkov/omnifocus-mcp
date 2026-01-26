"""Reorder tasks tool for OmniFocus."""

from typing import Any

from ..response import omnijs_json_response


async def reorder_tasks(
    container_id: str,
    mode: str,
    container_type: str = "project",
    sort_by: str | None = None,
    sort_order: str = "asc",
    task_id: str | None = None,
    position: str | None = None,
    reference_task_id: str | None = None,
    task_ids: list[str] | None = None,
) -> str:
    """
    Reorder tasks within a project or parent task.

    Supports three modes:
    - sort: Sort all tasks by a field (name, dueDate, flagged, etc.)
    - move: Move a single task to a specific position
    - custom: Reorder tasks by providing task IDs in desired order

    Args:
        container_id: ID of the project or parent task containing the tasks
        mode: Reorder mode - 'sort', 'move', or 'custom'
        container_type: Type of container - 'project' or 'task' (default: 'project')

        For mode='sort':
            sort_by: Field to sort by - 'name', 'dueDate', 'deferDate', 'plannedDate',
                'flagged', 'estimatedMinutes'
            sort_order: Sort direction - 'asc' or 'desc' (default: 'asc')

        For mode='move':
            task_id: ID of the task to move
            position: Target position - 'beginning', 'ending', 'before', 'after'
            reference_task_id: ID of reference task (required for 'before'/'after')

        For mode='custom':
            task_ids: List of task IDs in the desired order

    Returns:
        JSON string with result:
        {
            "success": true,
            "message": "...",
            "taskCount": N
        }
        or {"error": "..."} on failure

    Examples:
        # Sort tasks in a project alphabetically
        reorder_tasks(container_id="abc123", mode="sort", sort_by="name")

        # Sort by due date descending
        reorder_tasks(container_id="abc123", mode="sort", sort_by="dueDate", sort_order="desc")

        # Move a task to the beginning
        reorder_tasks(container_id="abc123", mode="move", task_id="xyz789", position="beginning")

        # Move a task after another task
        reorder_tasks(
            container_id="abc123",
            mode="move",
            task_id="xyz789",
            position="after",
            reference_task_id="def456"
        )

        # Custom order
        reorder_tasks(container_id="abc123", mode="custom", task_ids=["id1", "id2", "id3"])

    Note:
        Reordering only works for tasks within projects or parent tasks.
        Reordering tasks in tag views or perspectives is not supported by OmniFocus.
    """
    params: dict[str, Any] = {
        "container_id": container_id,
        "container_type": container_type,
        "mode": mode,
    }

    if mode == "sort":
        if sort_by:
            params["sort_by"] = sort_by
        params["sort_order"] = sort_order
    elif mode == "move":
        if task_id:
            params["task_id"] = task_id
        if position:
            params["position"] = position
        if reference_task_id:
            params["reference_task_id"] = reference_task_id
    elif mode == "custom":
        if task_ids:
            params["task_ids"] = task_ids

    return await omnijs_json_response("reorder_tasks", params)
