"""Test CLI module."""

import json
import pytest
from unittest.mock import AsyncMock, patch

from omnifocus_mcp.cli import (
    _parse_json_arg,
    _print_result,
    app,
)


class TestParseJsonArg:
    """Tests for _parse_json_arg function."""

    def test_parse_valid_dict(self):
        """Test parsing a valid JSON object."""
        result = _parse_json_arg('{"key": "value"}', "test")
        assert result == {"key": "value"}

    def test_parse_valid_array(self):
        """Test parsing a valid JSON array."""
        result = _parse_json_arg('["a", "b", "c"]', "test")
        assert result == ["a", "b", "c"]

    def test_parse_valid_bool(self):
        """Test parsing a valid JSON boolean."""
        result = _parse_json_arg("true", "test")
        assert result is True

    def test_parse_valid_number(self):
        """Test parsing a valid JSON number."""
        result = _parse_json_arg("42", "test")
        assert result == 42

    def test_parse_nested_object(self):
        """Test parsing a nested JSON object."""
        result = _parse_json_arg('{"filters": {"flagged": true, "due_within": 3}}', "test")
        assert result == {"filters": {"flagged": True, "due_within": 3}}

    def test_parse_invalid_json_raises(self):
        """Test that invalid JSON raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            _parse_json_arg("not valid json", "test_param")
        assert "Invalid JSON for test_param" in str(exc_info.value)

    def test_parse_empty_object(self):
        """Test parsing an empty JSON object."""
        result = _parse_json_arg("{}", "test")
        assert result == {}

    def test_parse_empty_array(self):
        """Test parsing an empty JSON array."""
        result = _parse_json_arg("[]", "test")
        assert result == []


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
        # Get all registered command names from the help text
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

        expected_commands = [
            "add-task",
            "edit",
            "remove",
            "add-project",
            "batch-add",
            "batch-remove",
            "query",
            "list-perspectives",
            "get-perspective",
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
        assert "query_omnifocus" in captured.out
        assert "list_perspectives" in captured.out


class TestCallCommand:
    """Tests for the generic call command."""

    @patch("omnifocus_mcp.cli.query_omnifocus")
    def test_call_known_tool(self, mock_query, capsys):
        """Test calling a known tool."""
        mock_query.return_value = '{"count": 0, "items": []}'

        from omnifocus_mcp.cli import call_tool

        call_tool("query_omnifocus", '{"entity": "tasks"}')

        mock_query.assert_called_once_with(entity="tasks")

    def test_call_unknown_tool_exits(self, capsys):
        """Test calling an unknown tool exits with error."""
        from omnifocus_mcp.cli import call_tool
        import sys

        with pytest.raises(SystemExit) as exc_info:
            call_tool("nonexistent_tool", "{}")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Unknown tool" in captured.err

    def test_call_with_invalid_json_exits(self, capsys):
        """Test calling with invalid JSON exits with error."""
        from omnifocus_mcp.cli import call_tool
        import sys

        with pytest.raises(SystemExit) as exc_info:
            call_tool("query_omnifocus", "not json")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.err
