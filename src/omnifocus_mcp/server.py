"""OmniFocus MCP Server - Main server implementation."""

import sys
import argparse
from mcp.server.fastmcp import FastMCP

# Import tools from separate modules
from .tools_tasks import add_omnifocus_task, edit_item, remove_item
from .tools_projects import add_project
from .tools_debug import dump_database

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
        help="Enable expanded mode with additional debug tools (including dump_database)"
    )
    
    args = parser.parse_args()
    
    # Register tools based on configuration
    register_tools(expanded=args.expanded)
    
    # Run the server with stdio transport (stdin/stdout)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
