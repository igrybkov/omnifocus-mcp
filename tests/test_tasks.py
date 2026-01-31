"""Tests for task-related tools."""

from unittest.mock import AsyncMock, patch

import pytest

from omnifocus_mcp.mcp_tools.tasks.add_task import add_omnifocus_task
from omnifocus_mcp.mcp_tools.tasks.edit_item import edit_item
from omnifocus_mcp.mcp_tools.tasks.remove_item import remove_item


class TestAddOmniFocusTask:
    """Tests for add_omnifocus_task function."""

    @pytest.mark.asyncio
    async def test_add_task_to_inbox(self):
        """Test adding a task to inbox."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.add_task.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Task added successfully to inbox", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute
            result = await add_omnifocus_task(name="Test Task")

            # Verify
            assert "Task added successfully to inbox" in result
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_task_to_project(self):
        """Test adding a task to a specific project."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.add_task.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (
                b"Task added successfully to project: Work",
                b"",
            )
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute
            result = await add_omnifocus_task(name="Test Task", project="Work")

            # Verify
            assert "Task added successfully to project: Work" in result
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_task_with_note(self):
        """Test adding a task with a note."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.add_task.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Task added successfully to inbox", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute
            result = await add_omnifocus_task(name="Test Task", note="This is a note")

            # Verify
            assert "Task added successfully to inbox" in result
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_task_escapes_special_characters(self):
        """Test that special characters are properly escaped."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.add_task.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Task added successfully to inbox", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute with special characters
            result = await add_omnifocus_task(name='Task "with" quotes')

            # Verify
            assert "Task added successfully to inbox" in result
            # Check that osascript was called with escaped string
            call_args = mock_exec.call_args
            script = call_args[0][2]  # Third argument is the script
            assert '\\"' in script  # Quotes should be escaped

    @pytest.mark.asyncio
    async def test_add_task_error_handling(self):
        """Test error handling when AppleScript fails."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.add_task.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock to return error
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"AppleScript error")
            mock_process.returncode = 1
            mock_exec.return_value = mock_process

            # Execute
            result = await add_omnifocus_task(name="Test Task")

            # Verify error is reported
            assert "Error:" in result
            assert "AppleScript error" in result


class TestEditItem:
    """Tests for edit_item function."""

    @pytest.mark.asyncio
    async def test_edit_task_name(self):
        """Test editing a task name."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Task updated successfully", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute
            result = await edit_item(current_name="Old Name", new_name="New Name")

            # Verify
            assert "Task updated successfully" in result
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_task_complete(self):
        """Test marking a task as complete."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Task updated successfully", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute
            result = await edit_item(current_name="Test Task", mark_complete=True)

            # Verify
            assert "Task updated successfully" in result
            # Check that script contains completion logic
            call_args = mock_exec.call_args
            script = call_args[0][2]
            assert "true" in script.lower()

    @pytest.mark.asyncio
    async def test_edit_project(self):
        """Test editing a project."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Project updated successfully", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute
            result = await edit_item(
                current_name="Old Project", new_name="New Project", item_type="project"
            )

            # Verify
            assert "Project updated successfully" in result
            mock_exec.assert_called_once()


class TestEditItemParentChange:
    """Tests for edit_item parent change functionality."""

    @pytest.mark.asyncio
    async def test_edit_task_change_parent(self):
        """Test changing a task's parent."""
        with (
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
            ) as mock_exec,
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.move_task_to_parent"
            ) as mock_move_parent,
        ):
            # Setup mocks
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"task-123", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            mock_move_parent.return_value = (True, "Task moved to task: New Parent")

            # Execute
            result = await edit_item(id="task-123", new_parent_id="parent-456")

            # Verify
            assert "Task updated successfully" in result
            assert "moved to new parent" in result
            mock_move_parent.assert_called_once_with("task-123", "parent-456")

    @pytest.mark.asyncio
    async def test_edit_task_unnest_to_project_root(self):
        """Test un-nesting a task (moving to project root)."""
        with (
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
            ) as mock_exec,
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.move_task_to_parent"
            ) as mock_move_parent,
        ):
            # Setup mocks
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"task-123", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            mock_move_parent.return_value = (True, "Task moved to project root")

            # Execute with empty string to un-nest
            result = await edit_item(id="task-123", new_parent_id="")

            # Verify
            assert "Task updated successfully" in result
            assert "moved to project root" in result
            mock_move_parent.assert_called_once_with("task-123", "")

    @pytest.mark.asyncio
    async def test_edit_task_parent_change_failure(self):
        """Test handling parent change failure."""
        with (
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
            ) as mock_exec,
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.move_task_to_parent"
            ) as mock_move_parent,
        ):
            # Setup mocks
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"task-123", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            mock_move_parent.return_value = (False, "Parent not found")

            # Execute
            result = await edit_item(id="task-123", new_parent_id="invalid-id")

            # Verify error is reported but task edit succeeded
            assert "Task updated successfully" in result
            assert "parent change failed" in result
            assert "Parent not found" in result

    @pytest.mark.asyncio
    async def test_edit_task_parent_and_position_change(self):
        """Test changing both parent and position."""
        with (
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
            ) as mock_exec,
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.move_task_to_parent"
            ) as mock_move_parent,
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.move_task_to_position"
            ) as mock_move_position,
        ):
            # Setup mocks
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"task-123", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            mock_move_parent.return_value = (True, "Task moved to new parent")
            mock_move_position.return_value = (True, "Task moved to beginning")

            # Execute with both parent and position
            result = await edit_item(
                id="task-123", new_parent_id="parent-456", new_position="beginning"
            )

            # Verify both operations were called
            assert "Task updated successfully" in result
            assert "moved to new parent" in result
            assert "repositioned to beginning" in result
            mock_move_parent.assert_called_once_with("task-123", "parent-456")
            mock_move_position.assert_called_once_with("task-123", "beginning", None)


class TestRemoveItem:
    """Tests for remove_item function."""

    @pytest.mark.asyncio
    async def test_remove_task(self):
        """Test removing a task."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.remove_item.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Task removed successfully: Test Task", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute
            result = await remove_item(name="Test Task")

            # Verify
            assert "Task removed successfully" in result
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_project(self):
        """Test removing a project."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.remove_item.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (
                b"Project removed successfully: Test Project",
                b"",
            )
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute
            result = await remove_item(name="Test Project", item_type="project")

            # Verify
            assert "Project removed successfully" in result
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_item_escapes_special_characters(self):
        """Test that special characters in item name are properly escaped."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.remove_item.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Task removed successfully", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute with special characters
            result = await remove_item(name='Task "with" quotes')

            # Verify
            assert "Task removed successfully" in result
            # Check that osascript was called with escaped string
            call_args = mock_exec.call_args
            script = call_args[0][2]
            assert '\\"' in script
