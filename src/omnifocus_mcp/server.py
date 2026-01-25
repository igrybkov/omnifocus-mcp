"""OmniFocus MCP Server - Main server implementation."""

import argparse

from mcp.server.fastmcp import FastMCP

from .mcp_tools.batch.batch_add import batch_add_items
from .mcp_tools.batch.batch_remove import batch_remove_items
from .mcp_tools.debug.dump_database import dump_database
from .mcp_tools.perspectives.get_perspective_view import get_perspective_view
from .mcp_tools.perspectives.list_perspectives import list_perspectives
from .mcp_tools.projects.add_project import add_project
from .mcp_tools.projects.tree import get_tree
from .mcp_tools.query.query import query_omnifocus

# Import tools from mcp_tools package
from .mcp_tools.tasks.add_task import add_omnifocus_task
from .mcp_tools.tasks.edit_item import edit_item
from .mcp_tools.tasks.remove_item import remove_item

# Create MCP server instance
mcp = FastMCP("OmniFocus MCP Server")


def register_tools(expanded: bool = False):
    """
    Register MCP tools based on configuration.

    Args:
        expanded: If True, include debug tools like dump_database
    """
    # Register core task tools
    mcp.tool()(add_omnifocus_task)
    mcp.tool()(edit_item)
    mcp.tool()(remove_item)

    # Register project tools
    mcp.tool()(add_project)
    mcp.tool()(get_tree)

    # Register batch tools
    mcp.tool()(batch_add_items)
    mcp.tool()(batch_remove_items)

    # Register query tools
    mcp.tool()(query_omnifocus)

    # Register perspective tools
    mcp.tool()(list_perspectives)
    mcp.tool()(get_perspective_view)

    # Register debug tools only if expanded mode is enabled
    if expanded:
        mcp.tool()(dump_database)


def main():
    """Main entry point for the MCP server."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="OmniFocus MCP Server")
    parser.add_argument(
        "--expanded",
        action="store_true",
        help="Enable expanded mode with additional debug tools (including dump_database)",
    )

    args = parser.parse_args()

    # Register tools based on configuration
    register_tools(expanded=args.expanded)

    # Run the server with stdio transport (stdin/stdout)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
