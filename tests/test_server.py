"""Tests for server module."""

from mcp.server.fastmcp import FastMCP

from omnifocus_mcp.server import TOOL_DEFAULTS, is_tool_enabled, mcp


class TestMcpFactory:
    """Tests for mcp factory function."""

    def test_mcp_returns_fastmcp_instance(self):
        """Test that mcp() returns a FastMCP instance."""
        server = mcp()
        assert isinstance(server, FastMCP)

    def test_mcp_has_correct_name(self):
        """Test that mcp() returns server with correct name."""
        server = mcp()
        assert server.name == "OmniFocus MCP Server"

    def test_mcp_registers_core_tools_by_default(self):
        """Test that core tools are registered by default."""
        server = mcp()
        expected_tools = [
            "add_omnifocus_task",
            "edit_item",
            "remove_item",
            "add_project",
            "add_folder",
            "browse",
            "batch_add_items",
            "batch_remove_items",
            "search",
            "list_perspectives",
            "get_perspective_view",
            "list_tags",
        ]

        for tool_name in expected_tools:
            assert tool_name in server._tool_manager._tools, f"Tool {tool_name} not registered"

    def test_mcp_excludes_dump_database_by_default(self, monkeypatch):
        """Test that dump_database is not registered by default."""
        monkeypatch.delenv("TOOL_DUMP_DATABASE", raising=False)
        server = mcp()
        assert "dump_database" not in server._tool_manager._tools

    def test_mcp_includes_dump_database_when_enabled(self, monkeypatch):
        """Test that dump_database is registered when env var is set."""
        monkeypatch.setenv("TOOL_DUMP_DATABASE", "true")
        server = mcp()
        assert "dump_database" in server._tool_manager._tools

    def test_mcp_can_disable_any_tool(self, monkeypatch):
        """Test that any tool can be disabled via env var."""
        monkeypatch.setenv("TOOL_SEARCH", "false")
        server = mcp()
        assert "search" not in server._tool_manager._tools


class TestIsToolEnabled:
    """Tests for is_tool_enabled function."""

    def test_tool_enabled_by_default(self, monkeypatch):
        """Test that tools without specific defaults are enabled."""
        monkeypatch.delenv("TOOL_ADD_OMNIFOCUS_TASK", raising=False)
        assert is_tool_enabled("add_omnifocus_task") is True

    def test_tool_disabled_by_default(self, monkeypatch):
        """Test that dump_database is disabled by default."""
        monkeypatch.delenv("TOOL_DUMP_DATABASE", raising=False)
        assert is_tool_enabled("dump_database") is False

    def test_env_var_enables_tool(self, monkeypatch):
        """Test that env var can enable a disabled-by-default tool."""
        for value in ("1", "true", "yes", "TRUE", "Yes"):
            monkeypatch.setenv("TOOL_DUMP_DATABASE", value)
            assert is_tool_enabled("dump_database") is True, f"Failed for value: {value}"

    def test_env_var_disables_tool(self, monkeypatch):
        """Test that env var can disable an enabled-by-default tool."""
        for value in ("0", "false", "no", "FALSE", "No"):
            monkeypatch.setenv("TOOL_ADD_OMNIFOCUS_TASK", value)
            assert is_tool_enabled("add_omnifocus_task") is False, f"Failed for value: {value}"


class TestToolDefaults:
    """Tests for TOOL_DEFAULTS configuration."""

    def test_dump_database_default_is_false(self):
        """Test that dump_database is disabled by default."""
        assert TOOL_DEFAULTS.get("dump_database") is False

    def test_other_tools_not_in_defaults(self):
        """Test that other tools are not in TOOL_DEFAULTS (meaning enabled by default)."""
        assert "add_omnifocus_task" not in TOOL_DEFAULTS
        assert "search" not in TOOL_DEFAULTS
