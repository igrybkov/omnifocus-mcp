"""Get perspective rules tool for OmniFocus."""

from ..response import omnijs_json_response


async def get_perspective_rules(
    perspective_name: str,
    resolve_ids: bool = True,
) -> str:
    """
    Get the filter rules for a custom OmniFocus perspective.

    Returns the rules that define what items appear in the perspective.
    Only works with custom perspectives (OmniFocus Pro feature).
    Built-in perspectives (Inbox, Projects, etc.) don't expose their rules.

    Args:
        perspective_name: Name of the custom perspective (case-insensitive)
        resolve_ids: If True, resolve tag and folder IDs to human-readable names
            (default: True). Set to False to get raw IDs only.

    Returns:
        JSON string with perspective rules in the following format:
        {
            "perspectiveName": "My Perspective",
            "perspectiveId": "abc123",
            "aggregation": "all" | "any" | "none" | null,
            "aggregationDescription": "Match ALL of the following rules",
            "ruleCount": 3,
            "rules": [
                {"actionAvailability": "available"},
                {"actionHasAnyOfTags": ["Work", "Urgent"], "_originalTagIds": ["id1", "id2"]},
                {"aggregateRules": [...], "aggregateType": "any"}
            ]
        }

    Common rule types:
        - actionAvailability: "available", "remaining", "completed"
        - actionStatus: "flagged", "due", "overdue"
        - actionHasAnyOfTags: List of tag names (or IDs if resolve_ids=False)
        - actionWithinFocus: List of folder/project names
        - actionIsProjectOrGroup: true/false
        - actionHasNoProject: true
        - actionHasDeferDate/actionHasDueDate/actionHasPlannedDate: true/false
        - actionDateField + actionDateIsToday/actionDateIsInTheNext/etc.
        - aggregateRules + aggregateType: Nested rule groups ("all", "any", "none")
        - disabledRule: Wrapper for rules that are disabled in the UI
    """
    return await omnijs_json_response(
        "get_perspective_rules",
        {
            "perspective_name": perspective_name,
            "resolve_ids": resolve_ids,
        },
    )
