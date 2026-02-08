"""Input validation utilities for OmniFocus MCP tools."""

from typing import Any

# Valid filter keys for each entity type (must match filters.js)
TASK_FILTER_KEYS = {
    "item_ids",
    "project_id",
    "project_name",
    "flagged",
    "tags",
    "status",
    "due_within",
    "due_after",
    "due_before",
    "deferred_until",
    "deferred_on",
    "planned_within",
    "has_note",
    "completed_within",
    "completed_after",
    "completed_before",
    "modified_before",
}

PROJECT_FILTER_KEYS = {
    "item_ids",
    "folder_id",
    "status",
    "available",
    "flagged",
    "sequential",
    "tags",
    "due_within",
    "due_after",
    "due_before",
    "deferred_until",
    "deferred_on",
    "has_note",
    "modified_before",
    "was_deferred",
    "stalled",
}


def validate_filters(filters: dict[str, Any], entity_type: str) -> None:
    """
    Validate filter keys against allowed sets.

    Args:
        filters: Filter dictionary to validate
        entity_type: Type being filtered ('tasks', 'projects')

    Raises:
        ValueError: If unknown filter keys are found
    """
    if not filters:
        return

    allowed_keys = TASK_FILTER_KEYS if entity_type == "tasks" else PROJECT_FILTER_KEYS
    unknown_keys = set(filters.keys()) - allowed_keys

    if unknown_keys:
        sorted_unknown = sorted(unknown_keys)
        sorted_valid = sorted(allowed_keys)
        raise ValueError(
            f"Unknown filter key(s) for {entity_type}: {', '.join(sorted_unknown)}. "
            f"Valid keys: {', '.join(sorted_valid)}"
        )
