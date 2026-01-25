"""CLI interface for running OmniFocus MCP tools directly from the shell."""

import asyncio
import inspect
import json
import sys
from collections.abc import Callable
from typing import Any, Union, get_args, get_origin

import cyclopts

from .server import mcp

# Create server instance with tools registered
_server = mcp()

app = cyclopts.App(
    name="omnifocus-cli",
    help="CLI interface for OmniFocus MCP tools. Run tools directly from the shell.",
)


def _get_tools_from_server() -> dict[str, tuple[Callable[..., Any], str]]:
    """Extract registered tools from the MCP server instance."""
    tools = {}
    for name, tool in _server._tool_manager._tools.items():
        # Get first line of description for short description
        desc = (tool.description or "").strip().split("\n")[0]
        tools[name] = (tool.fn, desc)
    return tools


def _func_name_to_cli_name(name: str) -> str:
    """Convert function name to CLI command name (snake_case -> kebab-case)."""
    return name.replace("_", "-")


def _is_json_type(hint: Any) -> bool:
    """Check if type hint requires JSON parsing (list or dict)."""
    if hint is None:
        return False

    origin = get_origin(hint)

    # Handle Union types (e.g., list[str] | None)
    if origin is Union:
        args = get_args(hint)
        return any(_is_json_type(arg) for arg in args if arg is not type(None))

    return origin in (list, dict) or hint in (list, dict)


def _print_result(result: str) -> None:
    """Print the result, attempting to pretty-print JSON."""
    try:
        parsed = json.loads(result)
        print(json.dumps(parsed, indent=2))
    except (json.JSONDecodeError, TypeError):
        print(result)


def _make_cli_command(func: Callable[..., Any]) -> Callable[..., None]:
    """
    Create a synchronous CLI wrapper from an async MCP tool function.

    Handles:
    - Converting async to sync via asyncio.run()
    - Parsing JSON string arguments for list/dict parameters
    - Pretty-printing results
    """
    hints = {k: v for k, v in func.__annotations__.items() if k != "return"}
    json_params = {k for k, v in hints.items() if _is_json_type(v)}
    sig = inspect.signature(func)

    def wrapper(*args: Any, **kwargs: Any) -> None:
        # Bind positional args to parameter names
        param_names = list(sig.parameters.keys())
        for i, arg in enumerate(args):
            if i < len(param_names):
                kwargs[param_names[i]] = arg

        # Parse JSON string parameters back to list/dict
        for param in json_params:
            value = kwargs.get(param)
            if value is not None and isinstance(value, str):
                try:
                    kwargs[param] = json.loads(value)
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON for {param}: {e}", file=sys.stderr)
                    sys.exit(1)

        result = asyncio.run(func(**kwargs))
        _print_result(result)

    # Build new annotations: transform list/dict types to str for CLI
    new_annotations: dict[str, Any] = {}
    for name, hint in hints.items():
        if name in json_params:
            origin = get_origin(hint)
            if origin is Union and type(None) in get_args(hint):
                new_annotations[name] = str | None
            else:
                new_annotations[name] = str
        else:
            new_annotations[name] = hint

    # Build new parameters with transformed types but same defaults
    new_params = []
    for param in sig.parameters.values():
        if param.name in new_annotations:
            new_params.append(
                param.replace(annotation=new_annotations.get(param.name, param.annotation))
            )
        else:
            new_params.append(param)

    new_sig = sig.replace(parameters=new_params, return_annotation=None)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__annotations__ = new_annotations
    wrapper.__signature__ = new_sig  # type: ignore[attr-defined]

    return wrapper


# Get tools from server and auto-register as CLI commands
_TOOLS = _get_tools_from_server()

for func_name, (func, _) in _TOOLS.items():
    cli_name = _func_name_to_cli_name(func_name)
    app.command(name=cli_name)(_make_cli_command(func))


@app.command(name="call")
def call_tool(tool_name: str, args: str = "{}") -> None:
    """Call any MCP tool by name with JSON arguments.

    Args:
        tool_name: Name of the tool to call (use list-tools to see available names)
        args: JSON object with tool arguments
    """
    if tool_name not in _TOOLS:
        print(f"Error: Unknown tool '{tool_name}'", file=sys.stderr)
        print(f"Available tools: {', '.join(sorted(_TOOLS.keys()))}", file=sys.stderr)
        sys.exit(1)

    try:
        kwargs = json.loads(args)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON for args: {e}", file=sys.stderr)
        sys.exit(1)

    func, _ = _TOOLS[tool_name]
    result = asyncio.run(func(**kwargs))
    _print_result(result)


@app.command(name="list-tools")
def list_tools() -> None:
    """List all available MCP tools."""
    print("Available MCP tools:")
    print()
    for name, (_, description) in sorted(_TOOLS.items()):
        print(f"  {name:25} {description}")
    print()
    print("Use 'omnifocus-cli call <tool_name> <json_args>' to call any tool directly.")
    print("Use 'omnifocus-cli <command> --help' for detailed command options.")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
