"""Get perspective view tool for OmniFocus."""

import json

from ...omnijs import execute_omnijs_with_params


async def get_perspective_view(
    perspective_name: str,
    limit: int = 100,
    include_metadata: bool = True,
    fields: list[str] | None = None,
) -> str:
    """
    Get the items visible in a specific OmniFocus perspective.

    Shows what tasks and projects are displayed when viewing that perspective.

    Args:
        perspective_name: Name of perspective to view (e.g., 'Inbox', 'Projects',
            'Flagged', or a custom perspective name)
        limit: Maximum number of items to return (default: 100)
        include_metadata: Include metadata like project names, tags, dates (default: True)
        fields: Specific fields to include (reduces response size).
            Available: id, name, note, flagged, dueDate, deferDate, completionDate,
            taskStatus, projectName, tagNames, estimatedMinutes

    Returns:
        JSON string with perspective content
    """
    default_fields = ["id", "name", "flagged", "dueDate", "taskStatus", "projectName", "tagNames"]
    fields_to_use = fields if fields else default_fields

    try:
        result = await execute_omnijs_with_params(
            "get_perspective_view",
            {
                "perspective_name": perspective_name,
                "limit": limit,
                "include_metadata": include_metadata,
                "fields": fields_to_use,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
