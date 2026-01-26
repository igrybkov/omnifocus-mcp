"""OmniFocus MCP Server - Main server implementation."""

import os

from mcp.server.fastmcp import FastMCP

from .mcp_tools.batch.batch_add import batch_add_items
from .mcp_tools.batch.batch_remove import batch_remove_items
from .mcp_tools.debug.dump_database import dump_database
from .mcp_tools.folders.add_folder import add_folder
from .mcp_tools.perspectives.get_perspective_rules import get_perspective_rules
from .mcp_tools.perspectives.get_perspective_view import get_perspective_view
from .mcp_tools.perspectives.list_perspectives import list_perspectives
from .mcp_tools.projects.add_project import add_project
from .mcp_tools.projects.browse import browse
from .mcp_tools.query.search import search
from .mcp_tools.reorder.reorder_tasks import reorder_tasks
from .mcp_tools.tags.list_tags import list_tags
from .mcp_tools.tasks.add_task import add_omnifocus_task
from .mcp_tools.tasks.edit_item import edit_item
from .mcp_tools.tasks.remove_item import remove_item

# Tool defaults: all enabled except dump_database
TOOL_DEFAULTS = {
    "dump_database": False,
}

# All available tools
_TOOLS = [
    add_omnifocus_task,
    edit_item,
    remove_item,
    add_project,
    add_folder,
    browse,
    batch_add_items,
    batch_remove_items,
    search,
    list_perspectives,
    get_perspective_view,
    get_perspective_rules,
    list_tags,
    reorder_tasks,
    dump_database,
]


def is_tool_enabled(tool_name: str) -> bool:
    """
    Check if a tool is enabled via environment variable.

    Environment variable format: TOOL_<TOOL_NAME_UPPERCASE>
    Example: TOOL_DUMP_DATABASE=true

    Args:
        tool_name: The tool function name (e.g., "dump_database")

    Returns:
        True if the tool should be registered, False otherwise
    """
    env_var = f"TOOL_{tool_name.upper()}"
    value = os.environ.get(env_var, "").lower()

    if value:
        return value in ("1", "true", "yes")

    # Use tool-specific default, or True if not specified
    return TOOL_DEFAULTS.get(tool_name, True)


def mcp() -> FastMCP:
    """
    Factory function for creating the MCP server.

    Creates a FastMCP instance and registers tools based on environment
    variable configuration. Each tool can be enabled/disabled via
    TOOL_<TOOL_NAME_UPPERCASE>=true/false.

    All tools are enabled by default except dump_database.

    Returns:
        Configured FastMCP server instance
    """
    server = FastMCP("OmniFocus MCP Server")

    for tool_fn in _TOOLS:
        if is_tool_enabled(tool_fn.__name__):
            server.tool()(tool_fn)

    return server


def main():
    """Main entry point for the MCP server."""
    server = mcp()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
