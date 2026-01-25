"""CLI interface for running OmniFocus MCP tools directly from the shell."""

import asyncio
import json
import sys
from typing import Any

import cyclopts

from .mcp_tools.batch.batch_add import batch_add_items
from .mcp_tools.batch.batch_remove import batch_remove_items
from .mcp_tools.perspectives.get_perspective_view import get_perspective_view
from .mcp_tools.perspectives.list_perspectives import list_perspectives
from .mcp_tools.projects.add_project import add_project
from .mcp_tools.query.query import query_omnifocus
from .mcp_tools.tasks.add_task import add_omnifocus_task
from .mcp_tools.tasks.edit_item import edit_item
from .mcp_tools.tasks.remove_item import remove_item

app = cyclopts.App(
    name="omnifocus-cli",
    help="CLI interface for OmniFocus MCP tools. Run tools directly from the shell.",
)


def _parse_json_arg(value: str, param_name: str) -> Any:
    """Parse a JSON string argument."""
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for {param_name}: {e}") from e


def _print_result(result: str) -> None:
    """Print the result, attempting to pretty-print JSON."""
    try:
        parsed = json.loads(result)
        print(json.dumps(parsed, indent=2))
    except (json.JSONDecodeError, TypeError):
        print(result)


# Task commands
@app.command(name="add-task")
def add_task(
    name: str,
    *,
    note: str = "",
    project: str = "",
    due_date: str | None = None,
    defer_date: str | None = None,
    planned_date: str | None = None,
    flagged: bool | None = None,
    estimated_minutes: int | None = None,
    tags: str | None = None,
    parent_task_id: str | None = None,
    parent_task_name: str | None = None,
) -> None:
    """Add a new task to OmniFocus.

    Args:
        name: Task name/title
        note: Optional note/description
        project: Optional project name (adds to inbox if not specified)
        due_date: Due date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        defer_date: Defer date in ISO format
        planned_date: Planned date in ISO format (OmniFocus 4.7+)
        flagged: Flag status
        estimated_minutes: Estimated time in minutes
        tags: JSON array of tag names, e.g. '["work", "urgent"]'
        parent_task_id: Parent task ID for creating subtasks
        parent_task_name: Parent task name for creating subtasks
    """
    tags_list = _parse_json_arg(tags, "tags") if tags else None
    result = asyncio.run(
        add_omnifocus_task(
            name=name,
            note=note,
            project=project,
            due_date=due_date,
            defer_date=defer_date,
            planned_date=planned_date,
            flagged=flagged,
            estimated_minutes=estimated_minutes,
            tags=tags_list,
            parent_task_id=parent_task_id,
            parent_task_name=parent_task_name,
        )
    )
    _print_result(result)


@app.command(name="edit")
def edit(
    *,
    current_name: str = "",
    id: str | None = None,
    new_name: str = "",
    new_note: str = "",
    mark_complete: bool = False,
    item_type: str = "task",
    new_due_date: str | None = None,
    new_defer_date: str | None = None,
    new_planned_date: str | None = None,
    new_flagged: bool | None = None,
    new_estimated_minutes: int | None = None,
    new_status: str | None = None,
    add_tags: str | None = None,
    remove_tags: str | None = None,
    replace_tags: str | None = None,
    new_sequential: bool | None = None,
    new_folder_name: str | None = None,
    new_project_status: str | None = None,
) -> None:
    """Edit a task or project in OmniFocus.

    Args:
        current_name: Current name of the item (used if id not provided)
        id: ID of the item to edit (preferred)
        new_name: New name for the item
        new_note: New note for the item
        mark_complete: Mark item as complete (deprecated, use new_status)
        item_type: Type of item: 'task' or 'project'
        new_due_date: New due date in ISO format, empty to clear
        new_defer_date: New defer date in ISO format, empty to clear
        new_planned_date: New planned date in ISO format, empty to clear (tasks only)
        new_flagged: New flagged status
        new_estimated_minutes: New estimated minutes
        new_status: New status for tasks: 'incomplete', 'completed', 'dropped'
        add_tags: JSON array of tags to add, e.g. '["tag1", "tag2"]'
        remove_tags: JSON array of tags to remove
        replace_tags: JSON array of tags to replace all existing tags
        new_sequential: Whether the project should be sequential (projects only)
        new_folder_name: New folder to move the project to (projects only)
        new_project_status: New status for projects: 'active', 'completed', 'dropped', 'onHold'
    """
    add_tags_list = _parse_json_arg(add_tags, "add_tags") if add_tags else None
    remove_tags_list = _parse_json_arg(remove_tags, "remove_tags") if remove_tags else None
    replace_tags_list = _parse_json_arg(replace_tags, "replace_tags") if replace_tags else None

    result = asyncio.run(
        edit_item(
            current_name=current_name,
            id=id,
            new_name=new_name,
            new_note=new_note,
            mark_complete=mark_complete,
            item_type=item_type,
            new_due_date=new_due_date,
            new_defer_date=new_defer_date,
            new_planned_date=new_planned_date,
            new_flagged=new_flagged,
            new_estimated_minutes=new_estimated_minutes,
            new_status=new_status,
            add_tags=add_tags_list,
            remove_tags=remove_tags_list,
            replace_tags=replace_tags_list,
            new_sequential=new_sequential,
            new_folder_name=new_folder_name,
            new_project_status=new_project_status,
        )
    )
    _print_result(result)


@app.command(name="remove")
def remove(
    *,
    name: str = "",
    id: str | None = None,
    item_type: str = "task",
) -> None:
    """Remove a task or project from OmniFocus.

    Args:
        name: Name of the item (used if id not provided)
        id: ID of the item to remove (preferred)
        item_type: Type of item: 'task' or 'project'
    """
    result = asyncio.run(
        remove_item(
            name=name,
            id=id,
            item_type=item_type,
        )
    )
    _print_result(result)


# Project commands
@app.command(name="add-project")
def add_project_cmd(
    name: str,
    *,
    note: str = "",
    due_date: str | None = None,
    defer_date: str | None = None,
    flagged: bool | None = None,
    estimated_minutes: int | None = None,
    tags: str | None = None,
    folder_name: str | None = None,
    sequential: bool | None = None,
) -> None:
    """Add a new project to OmniFocus.

    Args:
        name: Project name
        note: Optional note/description
        due_date: Due date in ISO format
        defer_date: Defer date in ISO format
        flagged: Flag status
        estimated_minutes: Estimated time in minutes
        tags: JSON array of tag names
        folder_name: Folder name to add project to (root if not specified)
        sequential: Whether tasks should be sequential (default: parallel)
    """
    tags_list = _parse_json_arg(tags, "tags") if tags else None
    result = asyncio.run(
        add_project(
            name=name,
            note=note,
            due_date=due_date,
            defer_date=defer_date,
            flagged=flagged,
            estimated_minutes=estimated_minutes,
            tags=tags_list,
            folder_name=folder_name,
            sequential=sequential,
        )
    )
    _print_result(result)


# Batch commands
@app.command(name="batch-add")
def batch_add(
    items: str,
    *,
    create_sequentially: bool = True,
) -> None:
    """Add multiple tasks or projects in a single operation.

    Supports hierarchy through tempId/parentTempId references.

    Args:
        items: JSON array of items to add. Each item should have:
            - type: 'task' or 'project' (required)
            - name: Name of the item (required)
            - And any other properties supported by add_task/add_project
        create_sequentially: Process items in order for parent-child relationships
    """
    items_list = _parse_json_arg(items, "items")
    result = asyncio.run(
        batch_add_items(
            items=items_list,
            create_sequentially=create_sequentially,
        )
    )
    _print_result(result)


@app.command(name="batch-remove")
def batch_remove(items: str) -> None:
    """Remove multiple tasks or projects in a single operation.

    Args:
        items: JSON array of items to remove. Each item should have:
            - id: Optional ID of the item (preferred)
            - name: Optional name of the item
            - item_type: 'task' or 'project' (required)
    """
    items_list = _parse_json_arg(items, "items")
    result = asyncio.run(batch_remove_items(items=items_list))
    _print_result(result)


# Query commands
@app.command(name="query")
def query(
    entity: str,
    *,
    filters: str | None = None,
    fields: str | None = None,
    limit: int | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
    include_completed: bool = False,
    summary: bool = False,
) -> None:
    """Query OmniFocus database with powerful filters.

    Args:
        entity: Type to query: 'tasks', 'projects', or 'folders'
        filters: JSON object with filters:
            - project_id: Filter tasks by project ID
            - project_name: Filter tasks by project name (partial match)
            - folder_id: Filter projects by folder ID
            - tags: Filter by tag names (OR logic)
            - status: Filter by status (OR logic)
            - flagged: Filter by flagged status
            - due_within: Items due within N days
            - deferred_until: Items deferred within N days
            - planned_within: Tasks planned within N days
            - has_note: Filter by note presence
        fields: JSON array of specific fields to return
        limit: Maximum number of items to return
        sort_by: Field to sort by (name, dueDate, deferDate, etc.)
        sort_order: Sort order: 'asc' or 'desc'
        include_completed: Include completed/dropped items
        summary: Return only count of matches
    """
    filters_dict = _parse_json_arg(filters, "filters") if filters else None
    fields_list = _parse_json_arg(fields, "fields") if fields else None

    result = asyncio.run(
        query_omnifocus(
            entity=entity,
            filters=filters_dict,
            fields=fields_list,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            include_completed=include_completed,
            summary=summary,
        )
    )
    _print_result(result)


# Perspective commands
@app.command(name="list-perspectives")
def list_perspectives_cmd(
    *,
    include_built_in: bool = True,
    include_custom: bool = True,
) -> None:
    """List all available perspectives in OmniFocus.

    Args:
        include_built_in: Include built-in perspectives (Inbox, Projects, etc.)
        include_custom: Include custom perspectives (Pro feature)
    """
    result = asyncio.run(
        list_perspectives(
            include_built_in=include_built_in,
            include_custom=include_custom,
        )
    )
    _print_result(result)


@app.command(name="get-perspective")
def get_perspective(
    perspective_name: str,
    *,
    limit: int = 100,
    include_metadata: bool = True,
    fields: str | None = None,
) -> None:
    """Get items visible in a specific perspective.

    Args:
        perspective_name: Name of perspective (e.g., 'Inbox', 'Flagged', or custom name)
        limit: Maximum number of items to return
        include_metadata: Include project names, tags, dates, etc.
        fields: JSON array of specific fields to include
    """
    fields_list = _parse_json_arg(fields, "fields") if fields else None

    result = asyncio.run(
        get_perspective_view(
            perspective_name=perspective_name,
            limit=limit,
            include_metadata=include_metadata,
            fields=fields_list,
        )
    )
    _print_result(result)


# Generic call command for calling any tool with JSON arguments
@app.command(name="call")
def call_tool(tool_name: str, args: str = "{}") -> None:
    """Call any MCP tool by name with JSON arguments.

    Args:
        tool_name: Name of the tool to call
        args: JSON object with tool arguments
    """
    tools = {
        "add_omnifocus_task": add_omnifocus_task,
        "edit_item": edit_item,
        "remove_item": remove_item,
        "add_project": add_project,
        "batch_add_items": batch_add_items,
        "batch_remove_items": batch_remove_items,
        "query_omnifocus": query_omnifocus,
        "list_perspectives": list_perspectives,
        "get_perspective_view": get_perspective_view,
    }

    if tool_name not in tools:
        print(f"Error: Unknown tool '{tool_name}'", file=sys.stderr)
        print(f"Available tools: {', '.join(sorted(tools.keys()))}", file=sys.stderr)
        sys.exit(1)

    try:
        kwargs = _parse_json_arg(args, "args")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = asyncio.run(tools[tool_name](**kwargs))
    _print_result(result)


@app.command(name="list-tools")
def list_tools() -> None:
    """List all available MCP tools."""
    tools = [
        ("add_omnifocus_task", "Add a new task to OmniFocus"),
        ("edit_item", "Edit a task or project"),
        ("remove_item", "Remove a task or project"),
        ("add_project", "Add a new project"),
        ("batch_add_items", "Add multiple items at once"),
        ("batch_remove_items", "Remove multiple items at once"),
        ("query_omnifocus", "Query tasks, projects, or folders"),
        ("list_perspectives", "List available perspectives"),
        ("get_perspective_view", "Get items in a perspective"),
    ]

    print("Available MCP tools:")
    print()
    for name, description in tools:
        print(f"  {name:25} {description}")
    print()
    print("Use 'omnifocus-cli call <tool_name> <json_args>' to call any tool directly.")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
