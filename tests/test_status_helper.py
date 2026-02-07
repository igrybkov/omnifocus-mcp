"""Tests for task status change helper."""

from unittest.mock import patch

import pytest

from omnifocus_mcp.mcp_tools.tasks.status_helper import change_task_status


class TestChangeTaskStatus:
    """Tests for change_task_status helper."""

    @pytest.fixture
    def mock_execute(self):
        """Create a mock for execute_omnijs_with_params."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_complete_task(self, mock_execute):
        """Test marking a task as completed."""
        mock_execute.return_value = {
            "success": True,
            "message": "Task status changed to completed",
            "taskId": "task-123",
        }

        success, message = await change_task_status("task-123", "completed")

        assert success is True
        assert "completed" in message
        mock_execute.assert_called_once()
        params = mock_execute.call_args[0][1]
        assert params["task_id"] == "task-123"
        assert params["status"] == "completed"

    @pytest.mark.asyncio
    async def test_drop_task(self, mock_execute):
        """Test dropping a task."""
        mock_execute.return_value = {
            "success": True,
            "message": "Task status changed to dropped",
            "taskId": "task-123",
        }

        success, message = await change_task_status("task-123", "dropped")

        assert success is True
        assert "dropped" in message

    @pytest.mark.asyncio
    async def test_mark_incomplete(self, mock_execute):
        """Test marking a task as incomplete."""
        mock_execute.return_value = {
            "success": True,
            "message": "Task status changed to incomplete",
            "taskId": "task-123",
        }

        success, message = await change_task_status("task-123", "incomplete")

        assert success is True
        assert "incomplete" in message

    @pytest.mark.asyncio
    async def test_task_not_found(self, mock_execute):
        """Test error when task is not found."""
        mock_execute.return_value = {"error": "Task not found: bad-id"}

        success, message = await change_task_status("bad-id", "completed")

        assert success is False
        assert "not found" in message

    @pytest.mark.asyncio
    async def test_invalid_status(self, mock_execute):
        """Test error for invalid status value."""
        mock_execute.return_value = {"error": "Invalid status: bogus"}

        success, message = await change_task_status("task-123", "bogus")

        assert success is False
        assert "Invalid status" in message

    @pytest.mark.asyncio
    async def test_script_name(self, mock_execute):
        """Test that the correct script name is used."""
        mock_execute.return_value = {
            "success": True,
            "message": "Task status changed to completed",
            "taskId": "task-123",
        }

        await change_task_status("task-123", "completed")

        script_name = mock_execute.call_args[0][0]
        assert script_name == "change_task_status"
