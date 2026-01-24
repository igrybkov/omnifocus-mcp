"""Tests for debug tools."""

import pytest
from unittest.mock import AsyncMock, patch
from omnifocus_mcp.mcp_tools.debug.dump_database import dump_database


class TestDumpDatabase:
    """Tests for dump_database function."""
    
    @pytest.mark.asyncio
    async def test_dump_database_success(self):
        """Test successful database dump."""
        with patch('omnifocus_mcp.mcp_tools.debug.dump_database.asyncio.create_subprocess_exec') as mock_exec:
            # Setup mock
            mock_output = b"PROJECT: Test Project\n  Status: false\n  TASK: Test Task\n    Completed: false\n"
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_output, b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process
            
            # Execute
            result = await dump_database()
            
            # Verify
            assert "PROJECT: Test Project" in result
            assert "TASK: Test Task" in result
            mock_exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dump_database_error_handling(self):
        """Test error handling when AppleScript fails."""
        with patch('omnifocus_mcp.mcp_tools.debug.dump_database.asyncio.create_subprocess_exec') as mock_exec:
            # Setup mock to return error
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"AppleScript error")
            mock_process.returncode = 1
            mock_exec.return_value = mock_process
            
            # Execute
            result = await dump_database()
            
            # Verify error is reported
            assert "Error:" in result
            assert "AppleScript error" in result
    
    @pytest.mark.asyncio
    async def test_dump_database_exception_handling(self):
        """Test exception handling."""
        with patch('omnifocus_mcp.mcp_tools.debug.dump_database.asyncio.create_subprocess_exec') as mock_exec:
            # Setup mock to raise exception
            mock_exec.side_effect = Exception("Test exception")
            
            # Execute
            result = await dump_database()
            
            # Verify error is reported
            assert "Error dumping database:" in result
            assert "Test exception" in result
