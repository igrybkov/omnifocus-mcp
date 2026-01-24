# OmniFocus MCP Server

A Python-based Model Context Protocol (MCP) server that enables AI assistants like Claude to interact with OmniFocus on macOS. This server provides tools to read, create, edit, and delete tasks and projects in OmniFocus using natural language through AI assistants.

## Features

- 🔧 **Comprehensive OmniFocus Integration**: Add, edit, remove, and query tasks and projects
- 🐍 **Official Python MCP SDK**: Built using the official MCP SDK with FastMCP
- �� **Stdin/Stdout Transport**: Standard MCP stdio protocol for seamless integration
- ⚡ **UV Support**: Full support for UV package manager, including `uvx` for quick installation
- 🚀 **Easy Installation**: Install directly from GitHub with one command
- �� **Modular Design**: Tools organized in separate modules for better maintainability

## Installation

### Quick Start with uvx (Recommended)

Run the server without installing:

```bash
uvx --from git+https://github.com/igrybkov/omnifocus-mcp omnifocus-mcp
```

### Using UV

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install from GitHub
uv tool install git+https://github.com/igrybkov/omnifocus-mcp

# Run the server
omnifocus-mcp
```

### Using pip

```bash
pip install git+https://github.com/igrybkov/omnifocus-mcp
omnifocus-mcp
```

### Development Installation

```bash
git clone https://github.com/igrybkov/omnifocus-mcp.git
cd omnifocus-mcp
uv sync
uv run omnifocus-mcp
```

For local development, the repository includes a `.mcp.json` file for MCP client configuration.

## Usage

### With Claude Desktop

Add this configuration to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "omnifocus": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/igrybkov/omnifocus-mcp",
        "omnifocus-mcp"
      ]
    }
  }
}
```

Or if you installed with `uv tool install`:

```json
{
  "mcpServers": {
    "omnifocus": {
      "command": "omnifocus-mcp"
    }
  }
}
```

After updating the configuration, restart Claude Desktop.

### Available Tools

The server provides the following tools to interact with OmniFocus:

#### 1. `add_omnifocus_task`
Add a new task to OmniFocus.

**Parameters:**
- `name` (required): The task name
- `note` (optional): Task description/notes
- `project` (optional): Project name to add the task to

```
Example: "Add a task 'Review quarterly report' to my Work project"
```

#### 2. `add_project`
Create a new project in OmniFocus.

**Parameters:**
- `name` (required): The project name
- `note` (optional): Project description

```
Example: "Create a new project called 'Website Redesign'"
```

#### 3. `remove_item`
Remove a task or project from OmniFocus.

**Parameters:**
- `name` (required): Name of the task or project
- `item_type` (optional): "task" or "project" (default: "task")

```
Example: "Remove the task 'Buy groceries'"
```

#### 4. `edit_item`
Edit an existing task or project.

**Parameters:**
- `current_name` (required): Current name of the item
- `new_name` (optional): New name
- `new_note` (optional): New note/description
- `mark_complete` (optional): Mark as complete (boolean)
- `item_type` (optional): "task" or "project" (default: "task")

```
Example: "Mark the task 'Finish presentation' as complete"
Example: "Rename project 'Q1 Goals' to 'Q2 Goals'"
```

### Debug Tools (--expanded mode)

By default, the `dump_database` tool is hidden to prevent agents from using it unnecessarily. To enable it, run the server with the `--expanded` flag:

```bash
omnifocus-mcp --expanded
```

Or in Claude Desktop config:

```json
{
  "mcpServers": {
    "omnifocus": {
      "command": "omnifocus-mcp",
      "args": ["--expanded"]
    }
  }
}
```

#### `dump_database` (expanded mode only)
Export the current state of your OmniFocus database, including all projects and tasks.

**Note**: This tool is only available with the `--expanded` flag to avoid unnecessary database dumps.

```
Example: "Show me all my OmniFocus tasks"
```

## Project Structure

```
src/omnifocus_mcp/
├── __init__.py           # Package initialization
├── server.py             # Main server and tool registration
├── utils.py              # Utility functions (AppleScript escaping)
├── tools_tasks.py        # Task-related tools
├── tools_projects.py     # Project-related tools
└── tools_debug.py        # Debug tools (dump_database)
```

## Requirements

- macOS (OmniFocus is macOS-only)
- OmniFocus installed and running
- Python 3.10 or higher

## How It Works

This MCP server uses AppleScript to communicate with OmniFocus. When you make requests through Claude or another MCP client:

1. The client sends a request via stdin
2. The MCP server processes the request
3. AppleScript commands are executed to interact with OmniFocus
4. Results are returned via stdout to the client

All user inputs are properly escaped to prevent AppleScript injection attacks.

## Motivation & Design Philosophy

This project was inspired by [themotionmachine/OmniFocus-MCP](https://github.com/themotionmachine/OmniFocus-MCP), but created to address specific limitations:

### Key Improvements

- **Efficient Database Access**: The `dump_database` tool is hidden by default (requires `--expanded` flag) to prevent AI agents from unnecessarily dumping entire databases. This is critical for users with large OmniFocus databases where frequent dumps become a performance bottleneck.

- **Rapid Feature Adoption**: Independent development allows quick implementation of new OmniFocus features (like Planned dates) without waiting for upstream project maintainers.

- **Modular Architecture**: Tools are organized in separate modules for better maintainability and easier extension.

### Technical Stack

- **Python**: More convenient development experience with modern tooling
- **Official MCP SDK**: Uses FastMCP for cleaner, more maintainable code
- **UV Package Manager**: Modern Python package management with simple installation via `uvx`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this in your own projects!
