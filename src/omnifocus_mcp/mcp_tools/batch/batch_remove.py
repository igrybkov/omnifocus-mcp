"""Batch remove items tool for OmniFocus."""

import json
from typing import Any

from ..tasks.remove_item import remove_item


async def batch_remove_items(
    items: list[dict[str, Any]],
) -> str:
    """
    Remove multiple tasks or projects from OmniFocus in a single operation.

    Args:
        items: List of items to remove. Each item is a dict with:
            - id: Optional ID of the item (preferred)
            - name: Optional name of the item (used if id not provided)
            - item_type: Type of item: 'task' or 'project' (required)

    Returns:
        JSON string with results summary and per-item details
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

    # Build summary
    success_count = sum(1 for r in results if r.get("success"))
    failure_count = len(results) - success_count

    summary = {
        "total": len(items),
        "success": success_count,
        "failed": failure_count,
        "results": results,
    }

    return json.dumps(summary, indent=2)
