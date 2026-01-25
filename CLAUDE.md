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
- **Standard mode**: 13 core tools
- **Expanded mode** (`--expanded` flag): Adds dump_database debug tool (14 total)

## Tools Reference

### Task Tools
- `add_omnifocus_task` - Create tasks with full properties (dates incl. planned date, flags, tags, parent tasks)
- `edit_item` - Edit tasks/projects (dates incl. planned date, flags, tags, status, folder moves)
- `remove_item` - Delete tasks/projects by ID or name

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
- `search` - Powerful filtered queries (by project, tags, status, dates, planned_within, folderPath)
  - Date filters support natural language: "tomorrow", "next week", "in 3 days", etc.

### Perspective Tools
- `list_perspectives` - List built-in and custom perspectives
- `get_perspective_view` - View items in a specific perspective
- `get_perspective_rules` - Get filter rules for a custom perspective (read-only, OmniFocus 4.2+)

### Debug Tools (--expanded only)
- `dump_database` - Full database dump with formatting options

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

## Design Decisions

- **dump_database hidden by default**: Prevents AI agents from unnecessarily dumping large OmniFocus databases
- **No exceptions from tools**: All tools return error messages as strings rather than raising exceptions
- **Async subprocess calls**: Uses `asyncio.create_subprocess_exec` for non-blocking execution
- **OmniJS for queries**: More efficient than AppleScript for database-wide operations
- **Date handling outside tell blocks**: Required due to AppleScript limitations
