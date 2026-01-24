"""Tests for debug tools."""

import pytest
from unittest.mock import AsyncMock, patch
from omnifocus_mcp.mcp_tools.debug.dump_database import dump_database


class TestDumpDatabase:
    """Tests for dump_database function."""

    @pytest.mark.asyncio
    async def test_dump_database_success(self):
        """Test successful database dump."""
        with patch('omnifocus_mcp.mcp_tools.debug.dump_database.execute_omnijs') as mock_exec:
            # Setup mock - OmniJS returns the formatted output
            mock_output = "Legend: F:Folder P:Project\n\nP: Test Project\n  • Test Task"
            mock_exec.return_value = {"result": mock_output, "raw": True}

            # Execute
            result = await dump_database()

            # Verify
            assert "Test Project" in result
            assert "Test Task" in result
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_dump_database_with_hide_completed_false(self):
        """Test database dump with hide_completed=False."""
        with patch('omnifocus_mcp.mcp_tools.debug.dump_database.execute_omnijs') as mock_exec:
            mock_output = "Legend: F:Folder\n\nP: Test Project #compl"
            mock_exec.return_value = {"result": mock_output, "raw": True}

            result = await dump_database(hide_completed=False)

            assert "Test Project" in result
            # Verify the script was called with the correct parameter
            call_args = mock_exec.call_args[0][0]
            assert "const hideCompleted = false" in call_args

    @pytest.mark.asyncio
    async def test_dump_database_error_handling(self):
        """Test error handling when OmniJS returns an error."""
        with patch('omnifocus_mcp.mcp_tools.debug.dump_database.execute_omnijs') as mock_exec:
            mock_exec.return_value = {"error": "OmniJS error"}

            result = await dump_database()

            assert "Error:" in result
            assert "OmniJS error" in result

    @pytest.mark.asyncio
    async def test_dump_database_exception_handling(self):
        """Test exception handling."""
        with patch('omnifocus_mcp.mcp_tools.debug.dump_database.execute_omnijs') as mock_exec:
            mock_exec.side_effect = Exception("Test exception")

            result = await dump_database()

            assert "Error dumping database:" in result
            assert "Test exception" in result
