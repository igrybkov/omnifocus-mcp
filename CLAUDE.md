# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python MCP (Model Context Protocol) server that enables AI assistants to interact with OmniFocus via AppleScript and OmniJS. Built with FastMCP and the official MCP SDK.

## Commands

### Development

```bash
uv sync                    # Install dependencies
uv run omnifocus-mcp       # Run server (standard mode - 13 tools)
uv run omnifocus-mcp --expanded  # Run with debug tools (14 tools, includes dump_database)
```

### Testing

```bash
pytest                     # Run all tests
pytest -v                  # Verbose output
pytest tests/test_tasks.py # Run single test file
pytest -k "test_add"       # Run tests matching pattern
```

### Running Tools During Development

Three options for testing MCP tools interactively:

**Option A: MCP Inspector UI**
```bash
# Requires: pip install fastmcp (separate from mcp package)
fastmcp dev src/omnifocus_mcp/server.py
```
Launches web UI for interactively testing all tools.

**Option B: Direct Python Import (zero setup)**
```bash
python -c "
import asyncio
from omnifocus_mcp.mcp_tools.query.search import search
print(asyncio.run(search('tasks', filters={'flagged': True})))
"
```
Tools are just async functions - call them directly.

**Option C: CLI Commands**
```bash
# List all available tools
uv run omnifocus-cli list-tools

# Named subcommands with flags
uv run omnifocus-cli add-omnifocus-task --name "Buy groceries" --project "Shopping" --flagged
uv run omnifocus-cli search --entity tasks --filters '{"flagged": true}'
uv run omnifocus-cli list-perspectives
uv run omnifocus-cli get-perspective-view "Flagged"

# Generic call with JSON arguments
uv run omnifocus-cli call add_omnifocus_task '{"name": "Buy groceries", "project": "Shopping"}'
uv run omnifocus-cli call search '{"entity": "tasks", "filters": {"due_within": 3}}'
```

## Architecture

### Tool Organization

Tools are organized by domain in `src/omnifocus_mcp/mcp_tools/`:

```
mcp_tools/
├── tasks/           # add_omnifocus_task, edit_item, remove_item
├── projects/        # add_project, browse
├── batch/           # batch_add_items, batch_remove_items
├── query/           # search
├── perspectives/    # list_perspectives, get_perspective_view, get_perspective_rules
├── reorder/         # reorder_tasks
└── debug/           # dump_database (--expanded only)
```

### Scripting Approaches

The server uses two complementary scripting approaches:

1. **AppleScript** - For CRUD operations (add/edit/remove tasks/projects)
   - Simple, direct manipulation of OmniFocus objects
   - Date handling requires construction outside `tell` blocks

2. **OmniJS** (via JXA wrapper) - For queries and database inspection
   - Provides access to `flattenedTasks`, `flattenedProjects`, `flattenedFolders` globals
   - Required for `Perspective.BuiltIn.*` and `Perspective.Custom.all`
   - Used by: `search`, `browse`, `list_perspectives`, `get_perspective_view`, `get_perspective_rules`, `dump_database`

### Core Utilities

| File | Purpose |
|------|---------|
| `src/omnifocus_mcp/utils.py` | AppleScript string escaping |
| `src/omnifocus_mcp/dates.py` | Date parsing (ISO + natural language) and AppleScript date generation |
| `src/omnifocus_mcp/tags.py` | Tag add/remove/replace AppleScript generation |
| `src/omnifocus_mcp/omnijs.py` | OmniJS execution via JXA wrapper |
| `src/omnifocus_mcp/applescript_builder.py` | High-level AppleScript builders (dates, find clause, tags) |
| `src/omnifocus_mcp/mcp_tools/response.py` | OmniJS JSON response handling, batch summaries |

### Shared JavaScript Modules

Located in `src/omnifocus_mcp/scripts/common/`:

| File | Purpose |
|------|---------|
| `status_maps.js` | Task/project status enums to strings (full and abbreviated) |
| `filters.js` | Filter factory functions, `isWithinDays()`, `isOnDay()` date helpers |
| `field_mappers.js` | Field mapping for tasks/projects/folders, `getFolderPath()` |

### Patterns to Follow (IMPORTANT)

**For AppleScript-based tools (add/edit/remove operations):**
```python
from ...applescript_builder import process_date_params, generate_find_clause, generate_tag_modifications

# Process all dates in one call
date_params = process_date_params("theTask", due_date=..., defer_date=..., planned_date=...)
date_pre_script = date_params.pre_tell_script
in_tell_assignments = date_params.in_tell_assignments

# Generate find clause (escapes inputs internally)
find_clause = generate_find_clause("task", "theTask", item_id=id, item_name=name)

# Generate tag modifications
tag_mods, tag_changes = generate_tag_modifications("theTask", add_tags, remove_tags, replace_tags)
```

**For OmniJS-based tools (queries, perspectives):**
```python
from ..response import omnijs_json_response

# Includes parameter is optional - pass shared modules needed by the script
INCLUDES = ["common/status_maps", "common/filters", "common/field_mappers"]

async def my_tool(params...) -> str:
    return await omnijs_json_response("script_name", {"param": value}, includes=INCLUDES)
```

**For batch operations:**
```python
from ..response import build_batch_summary

results = [{"success": True, ...}, {"success": False, ...}]
return json.dumps(build_batch_summary(results), indent=2)
```

**For JavaScript scripts:**
- Use shared modules via includes parameter in Python
- Add `// Requires: common/status_maps.js` comment at top of script
- Use `taskStatusMap`/`projectStatusMap` for full status names
- Use `taskStatusMapAbbrev`/`projectStatusMapAbbrev` for compact output
- Use `isWithinDays(date, days, requirePastOrPresent)` for date range checks

### Testing OmniJS-Based Tools

When mocking OmniJS execution in tests, patch at the response module:
```python
with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
    mock_exec.return_value = {"count": 1, "items": [...]}
    result = await my_tool()
```

### Tool Registration

`server.py` uses FastMCP decorators to register tools:
- **Standard mode**: 14 core tools
- **Expanded mode** (`--expanded` flag): Adds dump_database debug tool (15 total)

## Tools Reference

### Task Tools
- `add_omnifocus_task` - Create tasks with full properties (dates incl. planned date, flags, tags, parent tasks, position)
- `edit_item` - Edit tasks/projects (dates incl. planned date, flags, tags, status, folder moves, parent changes, position)
- `remove_item` - Delete tasks/projects by ID or name
- `reorder_tasks` - Reorder tasks within a project or parent task (sort, move, or custom order)

### Project Tools
- `add_project` - Create projects with properties (dates, flags, tags, folder, sequential)
- `browse` - Hierarchical tree of folders, projects, and tasks with filtering. Supports:
  - `parent_id`/`parent_name` - Start from specific folder (partial name matching)
  - `summary=True` - Return only counts (projectCount, folderCount, taskCount)
  - `fields` - Select specific fields to reduce response size (includes `folderPath`)
  - `include_folders`/`include_projects`/`include_tasks` - Control what to include
  - `filters` - Project filters: status, flagged, sequential, tags, due_within, deferred_until, deferred_on, has_note, available
  - `task_filters` - Task filters (when include_tasks=True): flagged, tags, status, due_within, deferred_on, planned_within
  - Date filters support natural language: "tomorrow", "next week", "in 3 days", etc.

### Batch Tools
- `batch_add_items` - Bulk create tasks/projects with hierarchy support (tempId/parentTempId)
- `batch_remove_items` - Bulk delete tasks/projects

### Query Tools
- `search` - Powerful filtered queries with optional aggregation and grouping
  - Date filters support natural language: "tomorrow", "next week", "in 3 days", etc.
  - **Aggregation support**: Group results by any field and compute statistics per group
  - **Nested grouping**: Multi-level aggregations (e.g., group by status, then by folder)
  - **Filtered counts**: Conditional aggregations (e.g., count stuck projects per group)
  - **Examples**: Include sample items with each group for context

### Perspective Tools
- `list_perspectives` - List built-in and custom perspectives
- `get_perspective_view` - View items in a specific perspective
- `get_perspective_rules` - Get filter rules for a custom perspective (read-only, OmniFocus 4.2+)

### Reorder Tools
- `reorder_tasks` - Reorder tasks within a project or parent task. Supports three modes:
  - `sort`: Sort all tasks by a field (name, dueDate, deferDate, plannedDate, flagged, estimatedMinutes)
  - `move`: Move a single task to a specific position (beginning, ending, before, after)
  - `custom`: Reorder tasks by providing task IDs in desired order

### Debug Tools (--expanded only)
- `dump_database` - Full database dump with formatting options

## Optional Parameter Patterns

For optional parameters that modify existing values, follow this pattern:

| Value | Meaning |
|-------|---------|
| `None` | Don't change (skip this field) |
| `""` (empty string) | Clear the value |
| A valid value | Set to this value |

This applies to:
- Date fields (`new_due_date`, `new_defer_date`, `new_planned_date`)
- Parent/container changes (`new_parent_id`)

Examples:
```python
# Don't change due date (default)
edit_item(id="taskId", new_due_date=None)

# Clear the due date
edit_item(id="taskId", new_due_date="")

# Set a new due date
edit_item(id="taskId", new_due_date="2024-01-25")
```

## Changing Task Parent

Tasks can be moved to a different parent (task or project) using `edit_item`:

```python
# Move task to become a subtask of another task
edit_item(id="taskId", new_parent_id="parentTaskId")

# Move task to a project (as a direct child)
edit_item(id="taskId", new_parent_id="projectId")

# Un-nest: move subtask back to project root
edit_item(id="taskId", new_parent_id="")
```

**Notes:**
- The `new_parent_id` accepts either a task ID or project ID
- Use empty string to un-nest (move to containing project's root)
- Cannot move a task to itself or to one of its descendants
- Inbox tasks cannot be un-nested (they have no containing project)

## Task Positioning

Tasks can be positioned when creating or editing them:

```python
# Create task at beginning of project
add_omnifocus_task(name="First task", project="My Project", position="beginning")

# Create task after a specific task
add_omnifocus_task(
    name="New task",
    project="My Project",
    position="after",
    reference_task_id="existingTaskId"
)

# Move existing task to end
edit_item(id="taskId", new_position="ending")

# Move task before another task
edit_item(id="taskId", new_position="before", position_reference_task_id="refTaskId")
```

**Position values:**
- `beginning` - First task in the container
- `ending` - Last task in the container
- `before` - Before the reference task (requires `reference_task_id`)
- `after` - After the reference task (requires `reference_task_id`)

**Limitations:**
- Positioning only works for tasks in projects or parent tasks
- Inbox tasks cannot be repositioned
- Tag views and perspectives cannot be reordered (OmniFocus limitation)

## Reordering Multiple Tasks

Use `reorder_tasks` for bulk reordering:

```python
# Sort all tasks in a project by name
reorder_tasks(container_id="projectId", mode="sort", sort_by="name")

# Sort by due date descending (most urgent first)
reorder_tasks(container_id="projectId", mode="sort", sort_by="dueDate", sort_order="desc")

# Move a specific task to beginning
reorder_tasks(container_id="projectId", mode="move", task_id="taskId", position="beginning")

# Custom order - provide task IDs in desired order
reorder_tasks(container_id="projectId", mode="custom", task_ids=["id3", "id1", "id2"])

# Reorder subtasks within a parent task
reorder_tasks(container_id="parentTaskId", container_type="task", mode="sort", sort_by="name")
```

## Security: AppleScript Injection Prevention

All user input must pass through `utils.escape_applescript_string()` before being embedded in AppleScript. The function escapes backslashes first, then double quotes.

## Natural Language Date Support

Date filters (`due_within`, `deferred_until`, `deferred_on`, `planned_within`) in `search` and `browse` tools accept natural language:

```python
# All equivalent ways to search for tasks due within 3 days
search('tasks', filters={'due_within': 3})
search('tasks', filters={'due_within': 'in 3 days'})
search('tasks', filters={'due_within': '2024-01-28'})  # ISO date

# Natural language examples
search('tasks', filters={'due_within': 'tomorrow'})
search('tasks', filters={'due_within': 'next week'})
search('tasks', filters={'planned_within': 'this friday'})
search('tasks', filters={'deferred_on': 'today'})  # Tasks scheduled to start today
browse(filters={'deferred_until': 'next monday'})
```

Supported formats:
- Relative: "today", "tomorrow", "yesterday"
- Periods: "this week", "next week", "last week"
- Days: "next monday", "last friday"
- Offsets: "in 3 days", "2 weeks ago"
- ISO: "2024-01-25", "2024-01-25T14:30:00"

Uses the `dateparser` library with `PREFER_DATES_FROM: future` for ambiguous dates.

## Search Aggregation and Grouping

The `search` tool supports powerful aggregation capabilities to reduce token consumption and enable server-side data summarization. This is particularly useful for portfolio reviews, planning workflows, and dashboards.

### Basic Grouping

Group results by any field and count items per group:

```python
# Group projects by folder
search(
    entity="projects",
    group_by="folderName",
    aggregations={"count": "count"}
)

# Output:
{
    "entity": "projects",
    "groupedBy": "folderName",
    "groups": [
        {"folderName": "Work", "count": 15},
        {"folderName": "Personal", "count": 8},
        {"folderName": "Goals", "count": 6}
    ]
}
```

### Filtered Aggregations

Compute conditional counts within each group:

```python
# Count stuck projects per folder (not modified in 21+ days)
search(
    entity="projects",
    group_by="folderName",
    aggregations={
        "count": "count",
        "stuck_count": {"filter": {"modified_before": 21}, "aggregate": "count"}
    },
    filters={"status": ["Active"]}
)

# Output:
{
    "groups": [
        {"folderName": "Work", "count": 15, "stuck_count": 3},
        {"folderName": "Personal", "count": 8, "stuck_count": 1}
    ]
}
```

### Nested Grouping

Create multi-level aggregations for portfolio views:

```python
# Group by status, then by folder within each status
search(
    entity="projects",
    group_by="status",
    aggregations={
        "count": "count",
        "by_folder": {
            "group_by": "folderName",
            "count": "count",
            "stuck_count": {"filter": {"modified_before": 21}, "aggregate": "count"}
        }
    }
)

# Output:
{
    "groups": [
        {
            "status": "Active",
            "count": 23,
            "by_folder": [
                {"folderName": "Work", "count": 15, "stuck_count": 3},
                {"folderName": "Goals", "count": 8, "stuck_count": 1}
            ]
        },
        {
            "status": "OnHold",
            "count": 5,
            "by_folder": [...]
        }
    ]
}
```

### Including Examples

Include sample items with each group for context:

```python
# Group projects with 2 examples per group
search(
    entity="projects",
    group_by="folderName",
    aggregations={
        "count": "count",
        "examples": {
            "include_examples": 2,
            "example_fields": ["id", "name", "dueDate"]
        }
    }
)

# Output:
{
    "groups": [
        {
            "folderName": "Work",
            "count": 15,
            "examples": [
                {"id": "proj1", "name": "Auth refactor", "dueDate": "2026-02-15"},
                {"id": "proj2", "name": "Q1 Planning", "dueDate": null}
            ]
        }
    ]
}
```

### Real-World Use Cases

**Monthly Review - Portfolio Overview:**
```python
# Single query replacing multiple separate queries
search(
    entity="projects",
    group_by="status",
    aggregations={
        "count": "count",
        "by_folder": {
            "group_by": "folderName",
            "count": "count",
            "stuck_count": {"filter": {"modified_before": 21}, "aggregate": "count"}
        }
    },
    filters={"status": ["Active", "OnHold", "Done"]}
)
```
**Token savings: ~4,300 → 600 tokens (86% reduction)**

**Weekly Review - Overdue Tasks by Project:**
```python
search(
    entity="tasks",
    group_by="projectName",
    aggregations={
        "overdue_count": {"filter": {"due_within": -7}, "aggregate": "count"},
        "flagged_count": {"filter": {"flagged": True}, "aggregate": "count"},
        "examples": {
            "include_examples": 3,
            "example_fields": ["id", "name", "dueDate"]
        }
    }
)
```
**Token savings: ~1,800 → 200 tokens (89% reduction)**

**Daily Planning - Available Tasks Summary:**
```python
search(
    entity="tasks",
    group_by="projectName",
    aggregations={
        "due_today": {"filter": {"due_within": 0}, "aggregate": "count"},
        "flagged": {"filter": {"flagged": True}, "aggregate": "count"},
        "quick_wins": {"filter": {"estimated_minutes_less_than": 30}, "aggregate": "count"}
    },
    filters={"status": ["Available"]}
)
```
**Token savings: ~2,000 → 400 tokens (80% reduction)**

### Backward Compatibility

When `group_by` is not specified, `search` returns the original format with individual items:

```python
# Without aggregation - returns all items
search(entity="projects", filters={"status": ["Active"]})

# Output (original format):
{
    "count": 23,
    "entity": "projects",
    "items": [
        {"id": "...", "name": "...", "status": "Active", ...},
        ...
    ]
}
```

### Performance Notes

- Aggregation is performed server-side after filtering and sorting
- `limit` parameter is applied before aggregation
- Grouping with `include_examples` allows combining summary stats with representative samples
- Nested aggregations can be arbitrarily deep (group by status → folder → tags, etc.)

## Design Decisions

- **dump_database hidden by default**: Prevents AI agents from unnecessarily dumping large OmniFocus databases
- **No exceptions from tools**: All tools return error messages as strings rather than raising exceptions
- **Async subprocess calls**: Uses `asyncio.create_subprocess_exec` for non-blocking execution
- **OmniJS for queries**: More efficient than AppleScript for database-wide operations
- **Date handling outside tell blocks**: Required due to AppleScript limitations
