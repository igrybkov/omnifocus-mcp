"""Get tree tool - hierarchical view of folders, projects, and tasks."""

import json
from typing import Any

from ...omnijs import execute_omnijs_with_params


async def get_tree(
    parent_id: str | None = None,
    parent_name: str | None = None,
    filters: dict[str, Any] | None = None,
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
    Get a hierarchical tree of folders, projects, and tasks.

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
        include_completed: Include completed/dropped projects and tasks (default: False)
        max_depth: Maximum folder depth to traverse (None = unlimited)
        include_root_projects: Include projects at root level (not in any folder) (default: True)
        summary: If True, return only counts (projectCount, folderCount, taskCount) without tree
        fields: Specific project/task fields to return (reduces response size).
            Project fields: id, name, status, sequential, flagged, dueDate, deferDate,
            estimatedMinutes, taskCount, tagNames.
            Task fields: id, name, flagged, dueDate, deferDate, estimatedMinutes, tagNames,
            completed, note.
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
    try:
        result = await execute_omnijs_with_params(
            "tree",
            {
                "parent_id": parent_id,
                "parent_name": parent_name,
                "filters": filters or {},
                "include_completed": include_completed,
                "max_depth": max_depth,
                "include_root_projects": include_root_projects,
                "summary": summary,
                "fields": fields or [],
                "include_folders": include_folders,
                "include_projects": include_projects,
                "include_tasks": include_tasks,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
