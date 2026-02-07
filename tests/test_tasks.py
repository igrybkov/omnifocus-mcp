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
        """Test marking a task as complete delegates to OmniJS."""
        with (
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
            ) as mock_exec,
            patch("omnifocus_mcp.mcp_tools.tasks.edit_item.change_task_status") as mock_status,
        ):
            # Setup mocks - AppleScript returns task ID
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"task-123", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            mock_status.return_value = (True, "Task status changed to completed")

            # Execute
            result = await edit_item(current_name="Test Task", mark_complete=True)

            # Verify
            assert "Task updated successfully" in result
            mock_status.assert_called_once_with("task-123", "completed")

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
    """Tests for remove_item function (drops items instead of deleting)."""

    @pytest.mark.asyncio
    async def test_remove_task_by_name(self):
        """Test removing (dropping) a task by name uses OmniJS."""
        with (
            patch(
                "omnifocus_mcp.mcp_tools.tasks.remove_item.asyncio.create_subprocess_exec"
            ) as mock_exec,
            patch("omnifocus_mcp.mcp_tools.tasks.remove_item.change_task_status") as mock_status,
        ):
            # Setup mocks - AppleScript resolves name to ID
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"resolved-task-id", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            mock_status.return_value = (True, "Task status changed to dropped")

            # Execute
            result = await remove_item(name="Test Task")

            # Verify
            assert "Task dropped successfully" in result
            mock_status.assert_called_once_with("resolved-task-id", "dropped")

    @pytest.mark.asyncio
    async def test_remove_task_by_id(self):
        """Test removing (dropping) a task by ID uses OmniJS directly."""
        with patch("omnifocus_mcp.mcp_tools.tasks.remove_item.change_task_status") as mock_status:
            mock_status.return_value = (True, "Task status changed to dropped")

            # Execute
            result = await remove_item(id="task-123")

            # Verify - no AppleScript needed when ID is provided
            assert "Task dropped successfully" in result
            mock_status.assert_called_once_with("task-123", "dropped")

    @pytest.mark.asyncio
    async def test_remove_project(self):
        """Test removing (dropping) a project."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.remove_item.asyncio.create_subprocess_exec"
        ) as mock_exec:
            # Setup mock
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (
                b"Project dropped successfully: Test Project",
                b"",
            )
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Execute
            result = await remove_item(name="Test Project", item_type="project")

            # Verify
            assert "Project dropped successfully" in result
            mock_exec.assert_called_once()
            # Verify the script uses 'dropped status' instead of 'delete'
            call_args = mock_exec.call_args
            script = call_args[0][2]
            assert "set status of theItem to dropped status" in script
            assert "delete" not in script

    @pytest.mark.asyncio
    async def test_remove_item_escapes_special_characters(self):
        """Test that special characters in item name are properly escaped."""
        with (
            patch(
                "omnifocus_mcp.mcp_tools.tasks.remove_item.asyncio.create_subprocess_exec"
            ) as mock_exec,
            patch("omnifocus_mcp.mcp_tools.tasks.remove_item.change_task_status") as mock_status,
        ):
            # Setup mock - AppleScript resolves name to ID
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"task-id", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            mock_status.return_value = (True, "Task status changed to dropped")

            # Execute with special characters
            result = await remove_item(name='Task "with" quotes')

            # Verify
            assert "Task dropped successfully" in result
            # Check that osascript was called with escaped string for name resolution
            call_args = mock_exec.call_args
            script = call_args[0][2]
            assert '\\"' in script


class TestEditItemStatusViaOmniJS:
    """Tests for task status changes via OmniJS (fixes inbox task issue)."""

    @pytest.mark.asyncio
    async def test_complete_task_uses_omnijs(self):
        """Test that completing a task delegates to OmniJS."""
        with (
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
            ) as mock_exec,
            patch("omnifocus_mcp.mcp_tools.tasks.edit_item.change_task_status") as mock_status,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"task-123", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process
            mock_status.return_value = (True, "Task status changed to completed")

            result = await edit_item(id="task-123", new_status="completed")

            assert "Task updated successfully" in result
            assert "status (completed)" in result
            mock_status.assert_called_once_with("task-123", "completed")

    @pytest.mark.asyncio
    async def test_drop_task_uses_omnijs(self):
        """Test that dropping a task delegates to OmniJS."""
        with (
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
            ) as mock_exec,
            patch("omnifocus_mcp.mcp_tools.tasks.edit_item.change_task_status") as mock_status,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"task-123", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process
            mock_status.return_value = (True, "Task status changed to dropped")

            result = await edit_item(id="task-123", new_status="dropped")

            assert "Task updated successfully" in result
            mock_status.assert_called_once_with("task-123", "dropped")

    @pytest.mark.asyncio
    async def test_mark_incomplete_uses_omnijs(self):
        """Test that marking incomplete delegates to OmniJS."""
        with (
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
            ) as mock_exec,
            patch("omnifocus_mcp.mcp_tools.tasks.edit_item.change_task_status") as mock_status,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"task-123", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process
            mock_status.return_value = (True, "Task status changed to incomplete")

            result = await edit_item(id="task-123", new_status="incomplete")

            assert "Task updated successfully" in result
            mock_status.assert_called_once_with("task-123", "incomplete")

    @pytest.mark.asyncio
    async def test_status_change_failure_reported(self):
        """Test that OmniJS status change failure is reported."""
        with (
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
            ) as mock_exec,
            patch("omnifocus_mcp.mcp_tools.tasks.edit_item.change_task_status") as mock_status,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"task-123", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process
            mock_status.return_value = (False, "Task not found: task-123")

            result = await edit_item(id="task-123", new_status="completed")

            assert "status change failed" in result

    @pytest.mark.asyncio
    async def test_status_change_not_in_applescript(self):
        """Verify that AppleScript does NOT contain status change commands."""
        with (
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
            ) as mock_exec,
            patch("omnifocus_mcp.mcp_tools.tasks.edit_item.change_task_status") as mock_status,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"task-123", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process
            mock_status.return_value = (True, "Task status changed to completed")

            await edit_item(id="task-123", new_status="completed")

            script = mock_exec.call_args[0][2]
            assert "set completed of" not in script
            assert "set dropped of" not in script

    @pytest.mark.asyncio
    async def test_status_with_other_edits(self):
        """Test status change combined with other edits (name, flag)."""
        with (
            patch(
                "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
            ) as mock_exec,
            patch("omnifocus_mcp.mcp_tools.tasks.edit_item.change_task_status") as mock_status,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"task-123", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process
            mock_status.return_value = (True, "Task status changed to completed")

            result = await edit_item(
                id="task-123",
                new_name="Updated",
                new_flagged=True,
                new_status="completed",
            )

            # AppleScript should still set name and flagged
            script = mock_exec.call_args[0][2]
            assert "set name of" in script
            assert "set flagged of" in script
            # But NOT status
            assert "set completed of" not in script

            # OmniJS handles status
            mock_status.assert_called_once_with("task-123", "completed")
            assert "Task updated successfully" in result

    @pytest.mark.asyncio
    async def test_project_status_still_uses_applescript(self):
        """Test that project status changes are NOT affected (still use AppleScript)."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.edit_item.asyncio.create_subprocess_exec"
        ) as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (
                b"Project updated successfully. Changed: status (completed)",
                b"",
            )
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await edit_item(
                current_name="My Project",
                item_type="project",
                new_project_status="completed",
            )

            # Project completion should still be in AppleScript
            script = mock_exec.call_args[0][2]
            assert "set completed of" in script
            assert "Project updated successfully" in result


class TestRemoveItemViaOmniJS:
    """Tests for remove_item using OmniJS for tasks."""

    @pytest.mark.asyncio
    async def test_remove_task_omnijs_failure(self):
        """Test error handling when OmniJS status change fails."""
        with patch("omnifocus_mcp.mcp_tools.tasks.remove_item.change_task_status") as mock_status:
            mock_status.return_value = (False, "Task not found: bad-id")

            result = await remove_item(id="bad-id")

            assert "Error:" in result
            assert "Task not found" in result

    @pytest.mark.asyncio
    async def test_remove_task_name_resolution_failure(self):
        """Test error when AppleScript can't resolve task name to ID."""
        with patch(
            "omnifocus_mcp.mcp_tools.tasks.remove_item.asyncio.create_subprocess_exec"
        ) as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"Can't find task")
            mock_process.returncode = 1
            mock_exec.return_value = mock_process

            result = await remove_item(name="Nonexistent Task")

            assert "Error:" in result
