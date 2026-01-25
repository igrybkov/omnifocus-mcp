"""Browse tool - hierarchical view of folders, projects, and tasks."""

from typing import Any

from ..response import omnijs_json_response

# Shared JS modules for browse script
BROWSE_INCLUDES = [
    "common/status_maps",
    "common/filters",
    "common/field_mappers",
]


async def browse(
    parent_id: str | None = None,
    parent_name: str | None = None,
    filters: dict[str, Any] | None = None,
    task_filters: dict[str, Any] | None = None,
    include_completed: bool = False,
    max_depth: int | None = None,
    include_root_projects: bool = True,
    summary: bool = False,
    fields: list[str] | None = None,
    include_folders: bool = True,
    include_projects: bool = True,
    include_tasks: bool = False,
) -> str:
    """
    Browse the hierarchical tree of folders, projects, and tasks.

    Returns a tree structure showing the folder/project/task hierarchy in OmniFocus.
    Supports filtering by various criteria and starting from a specific folder.

    Args:
        parent_id: Start traversal from folder with this ID (optional)
        parent_name: Start traversal from folder with this name (optional, case-insensitive,
            supports partial matching - e.g. "Goals" matches "🎯 Goals")
        filters: Optional filters for projects (all AND logic):
            - status: Filter by project status (list, OR logic).
                      Values: 'Active', 'Done', 'Dropped', 'OnHold'
            - flagged: Filter by flagged status (boolean)
            - sequential: Filter by sequential setting (boolean)
            - tags: Filter by tag names (list, OR logic - project has ANY of the tags)
            - due_within: Projects due within N days from today
            - deferred_until: Projects deferred becoming available within N days
            - has_note: Filter by note presence (boolean)
            - available: Filter to Active projects that are not deferred (boolean)
        task_filters: Optional filters for tasks when include_tasks=True (all AND logic):
            - flagged: Filter by flagged status (boolean)
            - tags: Filter by tag names (list, OR logic)
            - status: Filter by task status (list, OR logic)
            - due_within: Tasks due within N days from today
            - planned_within: Tasks planned within N days from today
        include_completed: Include completed/dropped projects and tasks (default: False)
        max_depth: Maximum folder depth to traverse (None = unlimited)
        include_root_projects: Include projects at root level (not in any folder) (default: True)
        summary: If True, return only counts (projectCount, folderCount, taskCount) without tree
        fields: Specific project/task fields to return (reduces response size).
            Project fields: id, name, status, sequential, flagged, dueDate, deferDate,
            estimatedMinutes, taskCount, tagNames, folderPath.
            Task fields: id, name, flagged, dueDate, deferDate, estimatedMinutes, tagNames,
            completed, note, folderPath.
            If not specified, returns all fields.
        include_folders: Include folder nodes in the tree (default: True)
        include_projects: Include project nodes in the tree (default: True)
        include_tasks: Include tasks within each project (default: False).
            When True, projects will have a "tasks" array with their tasks.

    Returns:
        JSON string with hierarchical tree structure (or just counts if summary=True):
        {
            "tree": [
                {
                    "type": "folder",
                    "id": "...",
                    "name": "Folder Name",
                    "children": [
                        {"type": "project", "id": "...", "name": "Project", "tasks": [...]},
                        {"type": "folder", "id": "...", "name": "Subfolder", "children": [...]}
                    ]
                },
                {"type": "project", "id": "...", "name": "Root Project", ...}
            ],
            "projectCount": 10,
            "folderCount": 5,
            "taskCount": 42
        }
    """
    return await omnijs_json_response(
        "browse",
        {
            "parent_id": parent_id,
            "parent_name": parent_name,
            "filters": filters or {},
            "task_filters": task_filters or {},
            "include_completed": include_completed,
            "max_depth": max_depth,
            "include_root_projects": include_root_projects,
            "summary": summary,
            "fields": fields or [],
            "include_folders": include_folders,
            "include_projects": include_projects,
            "include_tasks": include_tasks,
        },
        includes=BROWSE_INCLUDES,
    )
