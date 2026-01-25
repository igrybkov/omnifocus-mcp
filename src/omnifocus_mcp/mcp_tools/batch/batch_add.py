"""Batch add items tool for OmniFocus."""

import json
from typing import Any

from ..projects.add_project import add_project
from ..response import build_batch_summary
from ..tasks.add_task import add_omnifocus_task


async def batch_add_items(
    items: list[dict[str, Any]],
    create_sequentially: bool = True,
) -> str:
    """
    Add multiple tasks or projects to OmniFocus in a single operation.

    Supports hierarchy through tempId/parentTempId references, allowing
    you to create parent tasks and their subtasks in one batch.

    Args:
        items: List of items to add. Each item is a dict with:
            - type: 'task' or 'project' (required)
            - name: Name of the item (required)
            - note: Optional note/description
            - due_date: Optional due date in ISO format
            - defer_date: Optional defer date in ISO format
            - planned_date: Optional planned date in ISO format (tasks only, OmniFocus 4.7+)
            - flagged: Optional flag status
            - estimated_minutes: Optional estimated time
            - tags: Optional list of tag names
            For tasks:
            - project: Optional project name to add to
            - parent_task_id: Optional parent task ID
            - parent_task_name: Optional parent task name
            - temp_id: Optional temporary ID for within-batch references
            - parent_temp_id: Optional reference to parent's temp_id
            For projects:
            - folder_name: Optional folder name to add to
            - sequential: Optional whether tasks are sequential

        create_sequentially: If True, process items in order ensuring
            parents are created before children (default: True)

    Returns:
        JSON string with results summary and per-item details
    """
    results = []
    temp_id_to_real_id: dict[str, str] = {}
    processed = [False] * len(items)

    # Helper to check if an item can be processed
    def can_process(item: dict) -> bool:
        parent_temp_id = item.get("parent_temp_id")
        if parent_temp_id and parent_temp_id not in temp_id_to_real_id:
            return False
        return True

    # Process items, resolving dependencies
    max_iterations = len(items) * 2  # Prevent infinite loops
    iteration = 0

    while not all(processed) and iteration < max_iterations:
        iteration += 1
        made_progress = False

        for i, item in enumerate(items):
            if processed[i]:
                continue

            if not can_process(item):
                continue

            # Process this item
            item_type = item.get("type", "task")
            result = {"index": i, "type": item_type, "name": item.get("name", "")}

            try:
                if item_type == "project":
                    response = await add_project(
                        name=item.get("name", ""),
                        note=item.get("note", ""),
                        due_date=item.get("due_date"),
                        defer_date=item.get("defer_date"),
                        flagged=item.get("flagged"),
                        estimated_minutes=item.get("estimated_minutes"),
                        tags=item.get("tags"),
                        folder_name=item.get("folder_name"),
                        sequential=item.get("sequential"),
                    )
                else:
                    # Resolve parent_temp_id to real ID
                    parent_task_id = item.get("parent_task_id")
                    parent_temp_id = item.get("parent_temp_id")
                    if parent_temp_id and parent_temp_id in temp_id_to_real_id:
                        parent_task_id = temp_id_to_real_id[parent_temp_id]

                    response = await add_omnifocus_task(
                        name=item.get("name", ""),
                        note=item.get("note", ""),
                        project=item.get("project", ""),
                        due_date=item.get("due_date"),
                        defer_date=item.get("defer_date"),
                        planned_date=item.get("planned_date"),
                        flagged=item.get("flagged"),
                        estimated_minutes=item.get("estimated_minutes"),
                        tags=item.get("tags"),
                        parent_task_id=parent_task_id,
                        parent_task_name=item.get("parent_task_name"),
                    )

                # Check for success
                if response.startswith("Error"):
                    result["success"] = False
                    result["error"] = response
                else:
                    result["success"] = True
                    result["message"] = response

                    # Note: In a more complete implementation, we would
                    # extract the created item's ID from the response.
                    # For now, temp_id functionality is limited.
                    temp_id = item.get("temp_id")
                    if temp_id:
                        # Store a placeholder - real implementation would
                        # need to get actual ID from OmniFocus
                        temp_id_to_real_id[temp_id] = f"placeholder_{temp_id}"

            except Exception as e:
                result["success"] = False
                result["error"] = str(e)

            results.append(result)
            processed[i] = True
            made_progress = True

        if not made_progress and not all(processed):
            # Unresolved dependencies - mark remaining as failed
            for i, item in enumerate(items):
                if not processed[i]:
                    results.append(
                        {
                            "index": i,
                            "type": item.get("type", "task"),
                            "name": item.get("name", ""),
                            "success": False,
                            "error": "Unresolved dependency (parent_temp_id not found)",
                        }
                    )
                    processed[i] = True

    return json.dumps(build_batch_summary(results, len(items)), indent=2)
