"""Tests for server module."""

import pytest
from unittest.mock import MagicMock, patch
from omnifocus_mcp.server import register_tools


class TestRegisterTools:
    """Tests for register_tools function."""

    def test_register_tools_without_expanded(self):
        """Test that tools are registered correctly without expanded flag."""
        with patch('omnifocus_mcp.server.mcp') as mock_mcp:
            # Setup mock
            mock_tool_decorator = MagicMock(return_value=lambda x: x)
            mock_mcp.tool.return_value = mock_tool_decorator

            # Execute
            register_tools(expanded=False)

            # Verify that tool() was called 9 times (no dump_database)
            # Tools: add_omnifocus_task, edit_item, remove_item, add_project,
            #        batch_add_items, batch_remove_items, query_omnifocus,
            #        list_perspectives, get_perspective_view
            assert mock_mcp.tool.call_count == 9

    def test_register_tools_with_expanded(self):
        """Test that tools are registered correctly with expanded flag."""
        with patch('omnifocus_mcp.server.mcp') as mock_mcp:
            # Setup mock
            mock_tool_decorator = MagicMock(return_value=lambda x: x)
            mock_mcp.tool.return_value = mock_tool_decorator

            # Execute
            register_tools(expanded=True)

            # Verify that tool() was called 10 times (includes dump_database)
            assert mock_mcp.tool.call_count == 10
