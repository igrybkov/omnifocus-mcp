"""Batch remove items tool for OmniFocus.

Note: This tool drops items (marks them as dropped) instead of physically deleting them.
This preserves data and allows recovery if needed.
"""

import json
from typing import Any

from ..response import build_batch_summary
from ..tasks.remove_item import remove_item


async def batch_remove_items(
    items: list[dict[str, Any]],
) -> str:
    """
    Remove multiple tasks or projects from OmniFocus in a single operation.

    Note: Items are dropped (marked as dropped status) rather than physically deleted.
    This preserves data and allows recovery if needed.

    Args:
        items: List of items to remove. Each item is a dict with:
            - id: Optional ID of the item (preferred)
            - name: Optional name of the item (used if id not provided)
            - item_type: Type of item: 'task' or 'project' (required)

    Returns:
        JSON string with results in the following format:
        {
            "total": <number of items attempted>,
            "success": <number of items dropped successfully>,
            "failed": <number of items that failed>,
            "results": [
                {
                    "index": <0-based position in input array>,
                    "type": "task" | "project",
                    "id": <item id if provided>,
                    "name": <item name>,
                    "success": true | false,
                    "message": <success message if success=true>,
                    "error": <error message if success=false>
                },
                ...
            ]
        }
    """
    results = []

    for i, item in enumerate(items):
        item_type = item.get("item_type", "task")
        item_id = item.get("id")
        item_name = item.get("name", "")

        result = {
            "index": i,
            "type": item_type,
            "id": item_id,
            "name": item_name,
        }

        try:
            response = await remove_item(
                name=item_name,
                id=item_id,
                item_type=item_type,
            )

            if response.startswith("Error"):
                result["success"] = False
                result["error"] = response
            else:
                result["success"] = True
                result["message"] = response

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        results.append(result)

    return json.dumps(build_batch_summary(results), indent=2)
