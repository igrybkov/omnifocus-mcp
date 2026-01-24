# Contributing to OmniFocus MCP Server

Thank you for your interest in contributing to the OmniFocus MCP Server! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/omnifocus-mcp.git
   cd omnifocus-mcp
   ```

## Development Setup

### Requirements
- macOS (OmniFocus is macOS-only)
- Python 3.10 or higher
- OmniFocus installed

### Setting Up Your Environment

Using UV (recommended):
```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run the server in development mode
uv run omnifocus-mcp
```

Using pip:
```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .

# Run the server
omnifocus-mcp
```

## Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following these guidelines:
   - Keep changes focused and atomic
   - Write clear, descriptive commit messages
   - Update documentation as needed
   - Add docstrings to new functions

3. Test your changes:
   ```bash
   # Build the package
   python3 -m build
   
   # Install and test
   pip install dist/omnifocus_mcp-*.whl
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Add: Brief description of your changes"
   ```

## Code Style

- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Write descriptive docstrings for functions and classes
- Keep functions focused and manageable in size

## Adding New Tools

When adding new OmniFocus tools:

1. Add the tool function in `src/omnifocus_mcp/server.py`
2. Use the `@mcp.tool()` decorator
3. Include comprehensive docstring with:
   - Tool description
   - Parameter descriptions (Args section)
   - Return value description
4. Use AppleScript for OmniFocus interaction
5. Handle errors gracefully

Example:
```python
@mcp.tool()
async def my_new_tool(param: str) -> str:
    """
    Brief description of what the tool does.
    
    Args:
        param: Description of the parameter
    
    Returns:
        Description of the return value
    """
    try:
        # Implementation
        pass
    except Exception as e:
        return f"Error: {str(e)}"
```

## Testing

Before submitting a pull request:

1. Test that the package builds successfully:
   ```bash
   python3 -m build
   ```

2. Test the CLI entry point:
   ```bash
   omnifocus-mcp
   ```

3. Test with an MCP client (like Claude Desktop) if possible

## Submitting a Pull Request

1. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create a pull request on GitHub
3. Provide a clear description of:
   - What changes you made
   - Why you made them
   - How to test them

## Questions?

If you have questions or need help, feel free to:
- Open an issue on GitHub
- Ask questions in your pull request

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help make the project welcoming for everyone

Thank you for contributing! 🎉
