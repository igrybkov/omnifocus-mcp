"""Test CLI module."""

import json
from unittest.mock import patch

import pytest

from omnifocus_mcp.cli import (
    _func_name_to_cli_name,
    _is_json_type,
    _print_result,
    app,
)


class TestIsJsonType:
    """Tests for _is_json_type function."""

    def test_list_type(self):
        """Test that list type is detected."""
        assert _is_json_type(list) is True

    def test_list_str_type(self):
        """Test that list[str] type is detected."""
        assert _is_json_type(list[str]) is True

    def test_dict_type(self):
        """Test that dict type is detected."""
        assert _is_json_type(dict) is True

    def test_dict_str_any_type(self):
        """Test that dict[str, Any] type is detected."""
        from typing import Any

        assert _is_json_type(dict[str, Any]) is True

    def test_optional_list_type(self):
        """Test that list[str] | None type is detected."""
        assert _is_json_type(list[str] | None) is True

    def test_str_type_not_json(self):
        """Test that str type is not detected as JSON."""
        assert _is_json_type(str) is False

    def test_int_type_not_json(self):
        """Test that int type is not detected as JSON."""
        assert _is_json_type(int) is False

    def test_optional_str_not_json(self):
        """Test that str | None type is not detected as JSON."""
        assert _is_json_type(str | None) is False

    def test_bool_type_not_json(self):
        """Test that bool type is not detected as JSON."""
        assert _is_json_type(bool) is False

    def test_none_type_not_json(self):
        """Test that None type is not detected as JSON."""
        assert _is_json_type(None) is False


class TestFuncNameToCliName:
    """Tests for _func_name_to_cli_name function."""

    def test_snake_to_kebab(self):
        """Test converting snake_case to kebab-case."""
        assert _func_name_to_cli_name("add_omnifocus_task") == "add-omnifocus-task"

    def test_single_word(self):
        """Test single word remains unchanged."""
        assert _func_name_to_cli_name("query") == "query"

    def test_multiple_underscores(self):
        """Test multiple underscores."""
        assert _func_name_to_cli_name("get_perspective_view") == "get-perspective-view"


class TestPrintResult:
    """Tests for _print_result function."""

    def test_print_valid_json(self, capsys):
        """Test printing valid JSON gets pretty-printed."""
        _print_result('{"key": "value"}')
        captured = capsys.readouterr()
        expected = json.dumps({"key": "value"}, indent=2)
        assert captured.out.strip() == expected

    def test_print_non_json(self, capsys):
        """Test printing non-JSON string."""
        _print_result("Task added successfully")
        captured = capsys.readouterr()
        assert captured.out.strip() == "Task added successfully"

    def test_print_nested_json(self, capsys):
        """Test printing nested JSON gets pretty-printed."""
        data = {"items": [{"id": 1}, {"id": 2}]}
        _print_result(json.dumps(data))
        captured = capsys.readouterr()
        expected = json.dumps(data, indent=2)
        assert captured.out.strip() == expected


class TestCLICommands:
    """Tests for CLI commands structure."""

    def test_app_has_expected_commands(self):
        """Test that the app has all expected commands."""
        import io
        import sys

        # Capture the help output
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            app(["--help"])
        except SystemExit:
            pass
        help_text = sys.stdout.getvalue()
        sys.stdout = old_stdout

        # Commands are now auto-generated from function names (kebab-case)
        expected_commands = [
            "add-omnifocus-task",
            "edit-item",
            "remove-item",
            "add-project",
            "browse",
            "batch-add-items",
            "batch-remove-items",
            "search",
            "list-perspectives",
            "get-perspective-view",
            "call",
            "list-tools",
        ]

        for cmd in expected_commands:
            assert cmd in help_text, f"Command '{cmd}' not found in help output"

    def test_list_tools_output(self, capsys):
        """Test list-tools command output."""
        from omnifocus_mcp.cli import list_tools

        list_tools()
        captured = capsys.readouterr()

        assert "Available MCP tools:" in captured.out
        assert "add_omnifocus_task" in captured.out
        assert "search" in captured.out
        assert "list_perspectives" in captured.out
        assert "browse" in captured.out


class TestCallCommand:
    """Tests for the generic call command."""

    @patch("omnifocus_mcp.cli._TOOLS")
    def test_call_known_tool(self, mock_tools, capsys):
        """Test calling a known tool."""
        from unittest.mock import AsyncMock

        mock_query = AsyncMock(return_value='{"count": 0, "items": []}')
        mock_tools.__contains__ = lambda self, key: key == "query_omnifocus"
        mock_tools.__getitem__ = lambda self, key: (mock_query, "Query tasks")

        from omnifocus_mcp.cli import call_tool

        call_tool("query_omnifocus", '{"entity": "tasks"}')

        mock_query.assert_called_once_with(entity="tasks")

    def test_call_unknown_tool_exits(self, capsys):
        """Test calling an unknown tool exits with error."""

        from omnifocus_mcp.cli import call_tool

        with pytest.raises(SystemExit) as exc_info:
            call_tool("nonexistent_tool", "{}")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Unknown tool" in captured.err

    def test_call_with_invalid_json_exits(self, capsys):
        """Test calling with invalid JSON exits with error."""

        from omnifocus_mcp.cli import call_tool

        with pytest.raises(SystemExit) as exc_info:
            call_tool("search", "not json")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.err
