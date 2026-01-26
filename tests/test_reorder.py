"""Tests for reorder_tasks tool."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from omnifocus_mcp.mcp_tools.reorder.move_helper import move_task_to_position
from omnifocus_mcp.mcp_tools.reorder.reorder_tasks import reorder_tasks


class TestReorderTasks:
    """Tests for reorder_tasks function."""

    @pytest.fixture
    def mock_execute(self):
        """Create a mock for execute_omnijs_with_params."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_reorder_sort_by_name(self, mock_execute):
        """Test sorting tasks by name."""
        mock_execute.return_value = {
            "success": True,
            "message": "Sorted 5 tasks by name (asc)",
            "taskCount": 5,
        }

        result = await reorder_tasks(
            container_id="abc123",
            mode="sort",
            sort_by="name",
        )

        result_data = json.loads(result)
        assert result_data["success"] is True
        assert "Sorted 5 tasks" in result_data["message"]

        # Verify correct params were passed
        call_args = mock_execute.call_args
        assert call_args[0][0] == "reorder_tasks"
        params = call_args[0][1]
        assert params["container_id"] == "abc123"
        assert params["mode"] == "sort"
        assert params["sort_by"] == "name"
        assert params["sort_order"] == "asc"

    @pytest.mark.asyncio
    async def test_reorder_sort_descending(self, mock_execute):
        """Test sorting tasks in descending order."""
        mock_execute.return_value = {
            "success": True,
            "message": "Sorted 3 tasks by dueDate (desc)",
            "taskCount": 3,
        }

        await reorder_tasks(
            container_id="abc123",
            mode="sort",
            sort_by="dueDate",
            sort_order="desc",
        )

        call_args = mock_execute.call_args
        params = call_args[0][1]
        assert params["sort_by"] == "dueDate"
        assert params["sort_order"] == "desc"

    @pytest.mark.asyncio
    async def test_reorder_move_to_beginning(self, mock_execute):
        """Test moving a task to the beginning."""
        mock_execute.return_value = {
            "success": True,
            "message": "Moved task to beginning",
            "taskId": "task123",
        }

        result = await reorder_tasks(
            container_id="proj123",
            mode="move",
            task_id="task123",
            position="beginning",
        )

        result_data = json.loads(result)
        assert result_data["success"] is True

        params = mock_execute.call_args[0][1]
        assert params["mode"] == "move"
        assert params["task_id"] == "task123"
        assert params["position"] == "beginning"

    @pytest.mark.asyncio
    async def test_reorder_move_after_reference(self, mock_execute):
        """Test moving a task after another task."""
        mock_execute.return_value = {
            "success": True,
            "message": "Moved task to after",
            "taskId": "task123",
        }

        await reorder_tasks(
            container_id="proj123",
            mode="move",
            task_id="task123",
            position="after",
            reference_task_id="task456",
        )

        params = mock_execute.call_args[0][1]
        assert params["position"] == "after"
        assert params["reference_task_id"] == "task456"

    @pytest.mark.asyncio
    async def test_reorder_custom_order(self, mock_execute):
        """Test custom ordering of tasks."""
        mock_execute.return_value = {
            "success": True,
            "message": "Reordered 3 tasks in custom order",
            "taskCount": 3,
        }

        task_ids = ["task3", "task1", "task2"]
        result = await reorder_tasks(
            container_id="proj123",
            mode="custom",
            task_ids=task_ids,
        )

        result_data = json.loads(result)
        assert result_data["taskCount"] == 3

        params = mock_execute.call_args[0][1]
        assert params["mode"] == "custom"
        assert params["task_ids"] == task_ids

    @pytest.mark.asyncio
    async def test_reorder_with_parent_task_container(self, mock_execute):
        """Test reordering within a parent task (subtasks)."""
        mock_execute.return_value = {
            "success": True,
            "message": "Sorted 2 tasks by name (asc)",
            "taskCount": 2,
        }

        await reorder_tasks(
            container_id="parent123",
            container_type="task",
            mode="sort",
            sort_by="name",
        )

        params = mock_execute.call_args[0][1]
        assert params["container_type"] == "task"

    @pytest.mark.asyncio
    async def test_reorder_error_handling(self, mock_execute):
        """Test error handling when container not found."""
        mock_execute.return_value = {"error": "Project not found with ID: invalid123"}

        result = await reorder_tasks(
            container_id="invalid123",
            mode="sort",
            sort_by="name",
        )

        result_data = json.loads(result)
        assert "error" in result_data
        assert "not found" in result_data["error"]


class TestMoveTaskToPosition:
    """Tests for move_task_to_position helper."""

    @pytest.fixture
    def mock_execute(self):
        """Create a mock for execute_omnijs_with_params."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_move_success(self, mock_execute):
        """Test successful task move."""
        mock_execute.return_value = {
            "success": True,
            "message": "Task moved to beginning",
            "taskId": "task123",
        }

        success, message = await move_task_to_position(
            task_id="task123",
            position="beginning",
        )

        assert success is True
        assert "moved" in message.lower()

    @pytest.mark.asyncio
    async def test_move_with_reference(self, mock_execute):
        """Test moving task with reference."""
        mock_execute.return_value = {
            "success": True,
            "message": "Task moved to after",
            "taskId": "task123",
        }

        success, message = await move_task_to_position(
            task_id="task123",
            position="after",
            reference_task_id="task456",
        )

        assert success is True

        call_args = mock_execute.call_args
        assert call_args[0][0] == "move_task"
        params = call_args[0][1]
        assert params["reference_task_id"] == "task456"

    @pytest.mark.asyncio
    async def test_move_error(self, mock_execute):
        """Test error during move."""
        mock_execute.return_value = {"error": "Task not found: invalid123"}

        success, message = await move_task_to_position(
            task_id="invalid123",
            position="beginning",
        )

        assert success is False
        assert "not found" in message


class TestAddTaskWithPosition:
    """Tests for add_omnifocus_task with position parameter."""

    @pytest.mark.asyncio
    async def test_add_task_with_position(self):
        """Test adding task with position."""
        with (
            patch("asyncio.create_subprocess_exec") as mock_exec,
            patch("omnifocus_mcp.mcp_tools.tasks.add_task.move_task_to_position") as mock_move,
        ):
            # Mock AppleScript execution (returns task ID)
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"newTaskId123", b"")
            mock_exec.return_value = mock_process

            # Mock move operation
            mock_move.return_value = (True, "Task moved to beginning")

            from omnifocus_mcp.mcp_tools.tasks.add_task import add_omnifocus_task

            result = await add_omnifocus_task(
                name="Test Task",
                project="Test Project",
                position="beginning",
            )

            # Verify move was called
            mock_move.assert_called_once_with("newTaskId123", "beginning", None)
            assert "positioned at beginning" in result

    @pytest.mark.asyncio
    async def test_add_task_position_not_supported_for_inbox(self):
        """Test that position is not supported for inbox tasks."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"inboxTaskId", b"")
            mock_exec.return_value = mock_process

            from omnifocus_mcp.mcp_tools.tasks.add_task import add_omnifocus_task

            result = await add_omnifocus_task(
                name="Test Task",
                position="beginning",
            )

            assert "not supported for inbox" in result


class TestEditItemWithPosition:
    """Tests for edit_item with position parameter."""

    @pytest.mark.asyncio
    async def test_edit_task_with_position(self):
        """Test editing task with new position."""
        with (
            patch("asyncio.create_subprocess_exec") as mock_exec,
            patch("omnifocus_mcp.mcp_tools.tasks.edit_item.move_task_to_position") as mock_move,
        ):
            # Mock AppleScript execution (returns task ID)
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"taskId123", b"")
            mock_exec.return_value = mock_process

            # Mock move operation
            mock_move.return_value = (True, "Task moved to ending")

            from omnifocus_mcp.mcp_tools.tasks.edit_item import edit_item

            result = await edit_item(
                id="taskId123",
                new_name="Updated Task",
                new_position="ending",
            )

            mock_move.assert_called_once_with("taskId123", "ending", None)
            assert "repositioned to ending" in result

    @pytest.mark.asyncio
    async def test_edit_task_with_position_after_reference(self):
        """Test editing task with position after reference."""
        with (
            patch("asyncio.create_subprocess_exec") as mock_exec,
            patch("omnifocus_mcp.mcp_tools.tasks.edit_item.move_task_to_position") as mock_move,
        ):
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"taskId123", b"")
            mock_exec.return_value = mock_process

            mock_move.return_value = (True, "Task moved to after")

            from omnifocus_mcp.mcp_tools.tasks.edit_item import edit_item

            result = await edit_item(
                id="taskId123",
                new_position="after",
                position_reference_task_id="refTask456",
            )

            mock_move.assert_called_once_with("taskId123", "after", "refTask456")
            assert "repositioned to after" in result
