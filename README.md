# OmniFocus MCP Server

A Python-based Model Context Protocol (MCP) server that enables AI assistants like Claude to interact with OmniFocus on macOS. This server provides tools to read, create, edit, and delete tasks and projects in OmniFocus using natural language through AI assistants.

> 🤖 This entire project was written by AI. Yes, even this sentence. The AI is quite proud of itself.

## Features

- 🔧 **Comprehensive OmniFocus Integration**: Add, edit, remove, and query tasks and projects
- 🐍 **Official Python MCP SDK**: Built using the official MCP SDK
- 🔌 **Stdin/Stdout Transport**: Standard MCP stdio protocol for seamless integration
- ⚡ **UV Support**: Full support for UV package manager, including `uvx` for quick installation
- 🚀 **Easy Installation**: Install directly from GitHub with one command
- 🧩 **Modular Design**: Tools organized in separate modules for better maintainability

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

The easiest way to configure Claude Desktop (just needs uv):

```bash
uv tool run --from git+https://github.com/igrybkov/omnifocus-mcp omnifocus-cli add-server ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Or manually add this to your config file (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

The server provides 10 tools to interact with OmniFocus (plus one debug tool for the brave):

#### Task Tools

| Tool | What it does |
|------|--------------|
| `add_omnifocus_task` | Create tasks with all the bells and whistles (dates, flags, tags, estimates, parent tasks) |
| `edit_item` | Edit tasks or projects (rename, dates, flags, tags, status changes) |
| `remove_item` | Delete tasks or projects by ID or name |

#### Project Tools

| Tool | What it does |
|------|--------------|
| `add_project` | Create projects with dates, flags, tags, folder placement, sequential setting |
| `browse` | Navigate the folder/project/task hierarchy with filtering |

#### Batch Tools

| Tool | What it does |
|------|--------------|
| `batch_add_items` | Bulk create tasks/projects with hierarchy support (for when you have a lot to do) |
| `batch_remove_items` | Bulk delete tasks/projects (for when you've done a lot) |

#### Query Tools

| Tool | What it does |
|------|--------------|
| `search` | Powerful filtered queries by project, tags, status, dates, and more |

#### Perspective Tools

| Tool | What it does |
|------|--------------|
| `list_perspectives` | List built-in and custom perspectives |
| `get_perspective_view` | View items in a specific perspective |

### Tool Configuration

Tools can be enabled/disabled via environment variables. All tools are enabled by default except `dump_database` (because AI agents love to dump entire databases when you least expect it).

**Format**: `TOOL_<TOOL_NAME_UPPERCASE>=true|false`

To enable the debug tool:

```json
{
  "mcpServers": {
    "omnifocus": {
      "command": "omnifocus-mcp",
      "env": {
        "TOOL_DUMP_DATABASE": "true"
      }
    }
  }
}
```

To disable specific tools:

```json
{
  "mcpServers": {
    "omnifocus": {
      "command": "omnifocus-mcp",
      "env": {
        "TOOL_BATCH_REMOVE_ITEMS": "false"
      }
    }
  }
}
```

#### Debug Tool

| Tool | What it does |
|------|--------------|
| `dump_database` | Export the entire OmniFocus database (disabled by default, enable at your own risk) |

### CLI Interface

There's also a CLI for testing tools and managing configuration. Run without installing:

```bash
# Shorthand for examples below
alias omnifocus-cli='uv tool run --from git+https://github.com/igrybkov/omnifocus-mcp omnifocus-cli'

# Add server to an MCP config file
omnifocus-cli add-server ~/Library/Application\ Support/Claude/claude_desktop_config.json

# List available tools
omnifocus-cli list-tools

# Run tools with named flags
omnifocus-cli add-omnifocus-task --name "Buy groceries" --project "Shopping" --flagged
omnifocus-cli search --entity tasks --filters '{"flagged": true}'

# Generic call with JSON arguments
omnifocus-cli call search '{"entity": "tasks", "filters": {"due_within": 3}}'
```

## Project Structure

```
src/omnifocus_mcp/
├── server.py                # Main server and tool registration
├── cli.py                   # CLI interface
├── utils.py                 # Utility functions (AppleScript escaping)
├── dates.py                 # Date parsing and AppleScript generation
├── tags.py                  # Tag modification AppleScript
├── omnijs.py                # OmniJS execution via JXA
├── applescript_builder.py   # High-level AppleScript builders
├── scripts/                 # OmniJS scripts
│   └── common/              # Shared JS modules
└── mcp_tools/
    ├── tasks/               # add_task, edit_item, remove_item
    ├── projects/            # add_project, browse
    ├── batch/               # batch_add, batch_remove
    ├── query/               # search
    ├── perspectives/        # list_perspectives, get_perspective_view
    └── debug/               # dump_database
```

## Development

### Running Tests

The project includes a comprehensive test suite using pytest:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_tasks.py

# Run with coverage
pytest --cov=omnifocus_mcp
```

## Requirements

- macOS (OmniFocus is macOS-only)
- OmniFocus installed and running
- Python 3.10 or higher

## How It Works

This MCP server uses AppleScript for CRUD operations and OmniJS (via JXA) for queries. When you make requests through Claude or another MCP client:

1. The client sends a request via stdin
2. The MCP server processes the request
3. AppleScript/OmniJS commands are executed to interact with OmniFocus
4. Results are returned via stdout to the client

All user inputs are properly escaped to prevent AppleScript injection attacks.

## Motivation & Design Philosophy

This project was inspired by [themotionmachine/OmniFocus-MCP](https://github.com/themotionmachine/OmniFocus-MCP), but created to address specific limitations:

### Key Improvements

- **Efficient Database Access**: The `dump_database` tool is hidden by default to prevent AI agents from unnecessarily dumping entire databases. This is critical for users with large OmniFocus databases where frequent dumps become a performance bottleneck.

- **Rapid Feature Adoption**: Independent development allows quick implementation of new OmniFocus features (like Planned dates) without waiting for upstream project maintainers.

- **Modular Architecture**: Tools are organized in separate modules for better maintainability and easier extension.

### Technical Stack

- **Python**: More convenient development experience with modern tooling
- **Official MCP SDK**: Built with the official Python MCP SDK
- **UV Package Manager**: Modern Python package management with simple installation via `uvx`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. The AI promises not to be jealous.

## License

MIT License - feel free to use this in your own projects!
