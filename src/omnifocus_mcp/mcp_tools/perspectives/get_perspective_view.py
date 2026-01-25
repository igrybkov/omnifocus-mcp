"""Get perspective view tool for OmniFocus."""

from ..response import omnijs_json_response

# Shared JS modules for get_perspective_view script
PERSPECTIVE_VIEW_INCLUDES = ["common/status_maps"]


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
    default_fields = [
        "id",
        "name",
        "note",
        "flagged",
        "dueDate",
        "taskStatus",
        "projectName",
        "tagNames",
    ]
    fields_to_use = fields if fields else default_fields

    return await omnijs_json_response(
        "get_perspective_view",
        {
            "perspective_name": perspective_name,
            "limit": limit,
            "include_metadata": include_metadata,
            "fields": fields_to_use,
        },
        includes=PERSPECTIVE_VIEW_INCLUDES,
    )
