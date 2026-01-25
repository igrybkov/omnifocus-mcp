# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python MCP (Model Context Protocol) server that enables AI assistants to interact with OmniFocus via AppleScript and OmniJS. Built with FastMCP and the official MCP SDK.

## Commands

### Development

```bash
uv sync                    # Install dependencies
uv run omnifocus-mcp       # Run server (standard mode - 9 tools)
uv run omnifocus-mcp --expanded  # Run with debug tools (10 tools, includes dump_database)
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
from omnifocus_mcp.mcp_tools.query.query import query_omnifocus
print(asyncio.run(query_omnifocus('tasks', filters={'flagged': True})))
"
```
Tools are just async functions - call them directly.

**Option C: CLI Commands**
```bash
# List all available tools
uv run omnifocus-cli list-tools

# Named subcommands with flags
uv run omnifocus-cli add-task --name "Buy groceries" --project "Shopping" --flagged
uv run omnifocus-cli query --entity tasks --filters '{"flagged": true}'
uv run omnifocus-cli list-perspectives
uv run omnifocus-cli get-perspective "Flagged"

# Generic call with JSON arguments
uv run omnifocus-cli call add_omnifocus_task '{"name": "Buy groceries", "project": "Shopping"}'
uv run omnifocus-cli call query_omnifocus '{"entity": "tasks", "filters": {"due_within": 3}}'
```

## Architecture

### Tool Organization

Tools are organized by domain in `src/omnifocus_mcp/mcp_tools/`:

```
mcp_tools/
├── tasks/           # add_omnifocus_task, edit_item, remove_item
├── projects/        # add_project
├── batch/           # batch_add_items, batch_remove_items
├── query/           # query_omnifocus
├── perspectives/    # list_perspectives, get_perspective_view
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
   - Used by: `query_omnifocus`, `list_perspectives`, `get_perspective_view`, `dump_database`

### Core Utilities

| File | Purpose |
|------|---------|
| `src/omnifocus_mcp/utils.py` | AppleScript string escaping |
| `src/omnifocus_mcp/dates.py` | ISO date parsing and AppleScript date generation |
| `src/omnifocus_mcp/tags.py` | Tag add/remove/replace AppleScript generation |
| `src/omnifocus_mcp/omnijs.py` | OmniJS execution via JXA wrapper |

### Tool Registration

`server.py` uses FastMCP decorators to register tools:
- **Standard mode**: 9 core tools
- **Expanded mode** (`--expanded` flag): Adds dump_database debug tool

## Tools Reference

### Task Tools
- `add_omnifocus_task` - Create tasks with full properties (dates incl. planned date, flags, tags, parent tasks)
- `edit_item` - Edit tasks/projects (dates incl. planned date, flags, tags, status, folder moves)
- `remove_item` - Delete tasks/projects by ID or name

### Project Tools
- `add_project` - Create projects with properties (dates, flags, tags, folder, sequential)

### Batch Tools
- `batch_add_items` - Bulk create tasks/projects with hierarchy support (tempId/parentTempId)
- `batch_remove_items` - Bulk delete tasks/projects

### Query Tools
- `query_omnifocus` - Powerful filtered queries (by project, tags, status, dates, planned_within)

### Perspective Tools
- `list_perspectives` - List built-in and custom perspectives
- `get_perspective_view` - View items in a specific perspective

### Debug Tools (--expanded only)
- `dump_database` - Full database dump with formatting options

## Security: AppleScript Injection Prevention

All user input must pass through `utils.escape_applescript_string()` before being embedded in AppleScript. The function escapes backslashes first, then double quotes.

## Design Decisions

- **dump_database hidden by default**: Prevents AI agents from unnecessarily dumping large OmniFocus databases
- **No exceptions from tools**: All tools return error messages as strings rather than raising exceptions
- **Async subprocess calls**: Uses `asyncio.create_subprocess_exec` for non-blocking execution
- **OmniJS for queries**: More efficient than AppleScript for database-wide operations
- **Date handling outside tell blocks**: Required due to AppleScript limitations
