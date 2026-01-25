"""Tests for project-related tools."""

from unittest.mock import AsyncMock, patch

import pytest

from omnifocus_mcp.mcp_tools.projects.add_project import add_project


class TestAddProject:
    """Tests for add_project function."""

    @pytest.mark.asyncio
    async def test_add_project_basic(self):
        """Test adding a basic project."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.add_project.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (
                b"Project created successfully: Test Project",
                b"",
            )
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute
            result = await add_project(name="Test Project")

            # Verify
            assert "Project created successfully" in result
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_project_with_note(self):
        """Test adding a project with a note."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.add_project.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (
                b"Project created successfully: Test Project",
                b"",
            )
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute
            result = await add_project(name="Test Project", note="This is a project note")

            # Verify
            assert "Project created successfully" in result
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_project_escapes_special_characters(self):
        """Test that special characters are properly escaped."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.add_project.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Project created successfully", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute with special characters
            result = await add_project(name='Project "with" quotes')

            # Verify
            assert "Project created successfully" in result
            # Check that osascript was called with escaped string
            call_args = mock_exec.call_args
            script = call_args[0][2]
            assert '\\"' in script

    @pytest.mark.asyncio
    async def test_add_project_error_handling(self):
        """Test error handling when AppleScript fails."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.add_project.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock to return error
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"AppleScript error")
            mock_process.returncode = 1
            mock_exec.return_value = mock_process

            # Execute
            result = await add_project(name="Test Project")

            # Verify error is reported
            assert "Error:" in result
            assert "AppleScript error" in result
