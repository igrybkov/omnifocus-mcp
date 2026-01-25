"""Tests for search tool - query OmniFocus database."""

import json
from unittest.mock import patch

import pytest

from omnifocus_mcp.mcp_tools.query.search import search


class TestSearch:
    """Tests for search function."""

    @pytest.mark.asyncio
    async def test_search_tasks_basic(self):
        """Test basic task search."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "count": 2,
                "entity": "tasks",
                "items": [
                    {"id": "task1", "name": "Task 1", "flagged": True},
                    {"id": "task2", "name": "Task 2", "flagged": False},
                ],
            }

            result = await search(entity="tasks")
            result_data = json.loads(result)

            assert result_data["count"] == 2
            assert result_data["entity"] == "tasks"
            assert len(result_data["items"]) == 2
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_projects_basic(self):
        """Test basic project search."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "count": 1,
                "entity": "projects",
                "items": [
                    {"id": "proj1", "name": "Project 1", "status": "Active"},
                ],
            }

            result = await search(entity="projects")
            result_data = json.loads(result)

            assert result_data["count"] == 1
            assert result_data["entity"] == "projects"

    @pytest.mark.asyncio
    async def test_search_folders_basic(self):
        """Test basic folder search."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "count": 3,
                "entity": "folders",
                "items": [
                    {"id": "folder1", "name": "Work"},
                    {"id": "folder2", "name": "Personal"},
                    {"id": "folder3", "name": "Archive"},
                ],
            }

            result = await search(entity="folders")
            result_data = json.loads(result)

            assert result_data["count"] == 3
            assert result_data["entity"] == "folders"

    @pytest.mark.asyncio
    async def test_search_with_flagged_filter(self):
        """Test search with flagged filter."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 1, "entity": "tasks", "items": []}

            await search(entity="tasks", filters={"flagged": True})

            script_name, params, *_ = mock_exec.call_args[0]
            assert script_name == "search"
            assert params["filters"]["flagged"] is True

    @pytest.mark.asyncio
    async def test_search_with_tags_filter(self):
        """Test search with tags filter."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", filters={"tags": ["urgent", "work"]})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["tags"] == ["urgent", "work"]

    @pytest.mark.asyncio
    async def test_search_with_status_filter(self):
        """Test search with status filter."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", filters={"status": ["Available", "DueSoon"]})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["status"] == ["Available", "DueSoon"]

    @pytest.mark.asyncio
    async def test_search_with_project_id_filter(self):
        """Test search with project_id filter."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", filters={"project_id": "proj123"})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["project_id"] == "proj123"

    @pytest.mark.asyncio
    async def test_search_with_project_name_filter(self):
        """Test search with project_name filter."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", filters={"project_name": "Work"})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["project_name"] == "Work"

    @pytest.mark.asyncio
    async def test_search_with_folder_id_filter(self):
        """Test search with folder_id filter for projects."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "projects", "items": []}

            await search(entity="projects", filters={"folder_id": "folder123"})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["folder_id"] == "folder123"

    @pytest.mark.asyncio
    async def test_search_with_due_within_filter(self):
        """Test search with due_within filter."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", filters={"due_within": 7})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["due_within"] == 7

    @pytest.mark.asyncio
    async def test_search_with_deferred_until_filter(self):
        """Test search with deferred_until filter."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", filters={"deferred_until": 3})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["deferred_until"] == 3

    @pytest.mark.asyncio
    async def test_search_with_planned_within_filter(self):
        """Test search with planned_within filter."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", filters={"planned_within": 7})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["planned_within"] == 7

    @pytest.mark.asyncio
    async def test_search_with_has_note_filter(self):
        """Test search with has_note filter."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", filters={"has_note": True})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["has_note"] is True

    @pytest.mark.asyncio
    async def test_search_with_available_filter(self):
        """Test search with available filter for projects."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "projects", "items": []}

            await search(entity="projects", filters={"available": True})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["available"] is True

    @pytest.mark.asyncio
    async def test_search_with_fields(self):
        """Test search with specific fields."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", fields=["id", "name", "folderPath"])

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["fields"] == ["id", "name", "folderPath"]

    @pytest.mark.asyncio
    async def test_search_with_limit(self):
        """Test search with limit."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 10, "entity": "tasks", "items": []}

            await search(entity="tasks", limit=10)

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["limit"] == 10

    @pytest.mark.asyncio
    async def test_search_with_sort(self):
        """Test search with sorting."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", sort_by="dueDate", sort_order="desc")

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["sort_by"] == "dueDate"
            assert params["sort_order"] == "desc"

    @pytest.mark.asyncio
    async def test_search_include_completed(self):
        """Test search with include_completed=True."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", include_completed=True)

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["include_completed"] is True

    @pytest.mark.asyncio
    async def test_search_summary_mode(self):
        """Test search with summary=True returns only count."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 42, "entity": "tasks"}

            result = await search(entity="tasks", summary=True)
            result_data = json.loads(result)

            assert result_data["count"] == 42
            assert "items" not in result_data

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["summary"] is True

    @pytest.mark.asyncio
    async def test_search_error_handling(self):
        """Test error handling when OmniJS returns an error."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"error": "Search error: something went wrong"}

            result = await search(entity="tasks")
            result_data = json.loads(result)

            assert "error" in result_data

    @pytest.mark.asyncio
    async def test_search_exception_handling(self):
        """Test exception handling."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.side_effect = Exception("Test exception")

            result = await search(entity="tasks")
            result_data = json.loads(result)

            assert "error" in result_data
            assert "Test exception" in result_data["error"]

    @pytest.mark.asyncio
    async def test_search_uses_correct_script_name(self):
        """Test that the correct script name is used."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks")

            script_name, params, *_ = mock_exec.call_args[0]
            assert script_name == "search"

    @pytest.mark.asyncio
    async def test_search_passes_includes(self):
        """Test that search passes the includes parameter."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks")

            # Check that includes kwarg was passed
            call_kwargs = mock_exec.call_args[1]
            assert "includes" in call_kwargs
            assert "common/status_maps" in call_kwargs["includes"]
            assert "common/filters" in call_kwargs["includes"]
            assert "common/field_mappers" in call_kwargs["includes"]

    @pytest.mark.asyncio
    async def test_search_with_folder_path_field(self):
        """Test search returns folderPath when requested."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "count": 1,
                "entity": "projects",
                "items": [
                    {"id": "proj1", "name": "Project 1", "folderPath": ["Work", "Engineering"]}
                ],
            }

            result = await search(entity="projects", fields=["id", "name", "folderPath"])
            result_data = json.loads(result)

            assert result_data["items"][0]["folderPath"] == ["Work", "Engineering"]

    @pytest.mark.asyncio
    async def test_search_default_excludes_completed(self):
        """Test that search excludes completed items by default."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks")

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["include_completed"] is False

    @pytest.mark.asyncio
    async def test_search_default_sort_order_asc(self):
        """Test that default sort order is ascending."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", sort_by="name")

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["sort_order"] == "asc"
