# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python MCP (Model Context Protocol) server that enables AI assistants to interact with OmniFocus via AppleScript. Built with FastMCP and the official MCP SDK.

## Commands

### Development

```bash
uv sync                    # Install dependencies
uv run omnifocus-mcp       # Run server (standard mode)
uv run omnifocus-mcp --expanded  # Run with debug tools (includes dump_database)
```

### Testing

```bash
pytest                     # Run all tests
pytest -v                  # Verbose output
pytest tests/test_tasks.py # Run single test file
pytest -k "test_add"       # Run tests matching pattern
```

## Architecture

### Tool Organization

Tools are organized by domain in `src/omnifocus_mcp/mcp_tools/`:

```
mcp_tools/
├── tasks/           # add_task, edit_item, remove_item
├── projects/        # add_project
└── debug/           # dump_database (--expanded only)
```

Each tool is an async function that:
1. Takes typed parameters
2. Builds an AppleScript command
3. Executes via `asyncio.create_subprocess_exec("osascript", ...)`
4. Returns a success/error string (never raises exceptions)

### Tool Registration

`server.py` uses FastMCP decorators to register tools:
- **Standard mode**: 4 core tools (add_omnifocus_task, edit_item, remove_item, add_project)
- **Expanded mode** (`--expanded` flag): Adds dump_database debug tool

### Security: AppleScript Injection Prevention

All user input must pass through `utils.escape_applescript_string()` before being embedded in AppleScript. The function escapes backslashes first, then double quotes. Tests in `test_utils.py` verify injection protection.

## Key Files

| File | Purpose |
|------|---------|
| `src/omnifocus_mcp/server.py` | Entry point, CLI args, tool registration |
| `src/omnifocus_mcp/utils.py` | AppleScript string escaping |
| `pyproject.toml` | Dependencies, entry point: `omnifocus-mcp` |

## Design Decisions

- **dump_database hidden by default**: Prevents AI agents from unnecessarily dumping large OmniFocus databases. Use `--expanded` when debugging.
- **No exceptions from tools**: All tools return error messages as strings rather than raising exceptions, following MCP conventions.
- **Async subprocess calls**: Uses `asyncio.create_subprocess_exec` for non-blocking osascript execution.
