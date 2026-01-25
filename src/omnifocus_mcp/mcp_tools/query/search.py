"""Search OmniFocus database tool."""

from typing import Any

from ...dates import preprocess_date_filters
from ..response import omnijs_json_response

# Shared JS modules for search script
SEARCH_INCLUDES = [
    "common/status_maps",
    "common/filters",
    "common/field_mappers",
]


async def search(
    entity: str,
    filters: dict[str, Any] | None = None,
    fields: list[str] | None = None,
    limit: int | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
    include_completed: bool = False,
    summary: bool = False,
) -> str:
    """
    Search OmniFocus database with powerful filters.

    Much faster than dump_database for targeted queries.

    Args:
        entity: Type to query: 'tasks', 'projects', or 'folders'
        filters: Optional filters (all AND logic):
            - project_id: Filter tasks by exact project ID
            - project_name: Filter tasks by project name (case-insensitive partial match)
            - folder_id: Filter projects by exact folder ID
            - tags: Filter by tag names (exact match, OR logic between tags)
            - status: Filter by status (OR logic)
            - flagged: Filter by flagged status
            - due_within: Items due within N days from today. Supports natural language:
                "next 3 days", "this week", "tomorrow", or numeric days
            - deferred_until: Items deferred becoming available within N days.
                Supports natural language like due_within
            - deferred_on: Items where defer date equals specific date. Useful for
                finding "tasks scheduled to start today". Supports natural language
            - planned_within: Tasks planned within N days from today (OmniFocus 4.7+).
                Supports natural language like due_within
            - completed_within: Tasks completed within the last N days. Automatically
                enables include_completed. Supports natural language like due_within
            - modified_before: Items NOT modified in the last N days. Useful for
                finding stale items. Supports natural language like due_within
            - was_deferred: For projects, filter to Active projects that had a defer
                date in the past (have become available after being deferred)
            - has_note: Filter by note presence
            - available: For projects, filter to Active + not deferred
        fields: Specific fields to return (reduces response size). Task fields include:
            plannedDate, effectivePlannedDate, effectiveDueDate, effectiveDeferDate, folderPath
        limit: Maximum number of items to return
        sort_by: Field to sort by (name, dueDate, deferDate, plannedDate, modificationDate, etc.)
        sort_order: Sort order: 'asc' or 'desc' (default: 'asc')
        include_completed: Include completed/dropped items (default: False)
        summary: Return only count of matches (default: False)

    Returns:
        JSON string with query results or count
    """
    # Preprocess date filters to convert natural language to numeric days
    processed_filters = preprocess_date_filters(filters or {})

    # Auto-enable include_completed when completed_within is used
    if "completed_within" in processed_filters:
        include_completed = True

    return await omnijs_json_response(
        "search",
        {
            "entity": entity,
            "filters": processed_filters,
            "fields": fields,
            "limit": limit,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "include_completed": include_completed,
            "summary": summary,
        },
        includes=SEARCH_INCLUDES,
    )
