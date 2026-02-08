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
    async def test_search_with_item_ids_filter(self):
        """Test search with item_ids filter to fetch specific items by ID."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "count": 2,
                "entity": "tasks",
                "items": [
                    {"id": "task1", "name": "Task 1", "note": "Note 1"},
                    {"id": "task3", "name": "Task 3", "note": "Note 3"},
                ],
            }

            await search(
                entity="tasks",
                filters={"item_ids": ["task1", "task3"]},
                fields=["id", "name", "note"],
            )

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["item_ids"] == ["task1", "task3"]
            assert params["fields"] == ["id", "name", "note"]

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
    async def test_search_with_deferred_on_filter(self):
        """Test search with deferred_on filter for exact date match."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", filters={"deferred_on": 0})  # Today

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["deferred_on"] == 0

    @pytest.mark.asyncio
    async def test_search_with_deferred_on_natural_language(self):
        """Test search with deferred_on filter using natural language."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", filters={"deferred_on": "tomorrow"})

            script_name, params, *_ = mock_exec.call_args[0]
            # "tomorrow" should be converted to 1 day from today
            assert params["filters"]["deferred_on"] == 1

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

    # Aggregation tests
    @pytest.mark.asyncio
    async def test_search_with_group_by(self):
        """Test search with group_by parameter."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "entity": "projects",
                "groupedBy": "folderName",
                "groups": [
                    {"folderName": "Work", "count": 8},
                    {"folderName": "Personal", "count": 5},
                ],
            }

            result = await search(entity="projects", group_by="folderName")
            result_data = json.loads(result)

            assert result_data["entity"] == "projects"
            assert result_data["groupedBy"] == "folderName"
            assert len(result_data["groups"]) == 2
            assert result_data["groups"][0]["folderName"] == "Work"
            assert result_data["groups"][0]["count"] == 8

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["group_by"] == "folderName"

    @pytest.mark.asyncio
    async def test_search_with_group_by_and_aggregations(self):
        """Test search with group_by and custom aggregations."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "entity": "projects",
                "groupedBy": "status",
                "groups": [
                    {
                        "status": "Active",
                        "count": 23,
                        "stuck_count": 3,
                    },
                    {
                        "status": "OnHold",
                        "count": 5,
                        "stuck_count": 2,
                    },
                ],
            }

            aggregations = {
                "count": "count",
                "stuck_count": {"filter": {"modified_before": 21}, "aggregate": "count"},
            }

            result = await search(entity="projects", group_by="status", aggregations=aggregations)
            result_data = json.loads(result)

            assert result_data["groupedBy"] == "status"
            assert result_data["groups"][0]["stuck_count"] == 3
            assert result_data["groups"][1]["stuck_count"] == 2

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["aggregations"] == aggregations

    @pytest.mark.asyncio
    async def test_search_with_nested_aggregation(self):
        """Test search with nested grouping."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "entity": "projects",
                "groupedBy": "status",
                "groups": [
                    {
                        "status": "Active",
                        "count": 23,
                        "by_folder": [
                            {"folderName": "Work", "count": 15},
                            {"folderName": "Personal", "count": 8},
                        ],
                    },
                ],
            }

            aggregations = {
                "count": "count",
                "by_folder": {"group_by": "folderName", "count": "count"},
            }

            result = await search(entity="projects", group_by="status", aggregations=aggregations)
            result_data = json.loads(result)

            assert result_data["groups"][0]["by_folder"][0]["folderName"] == "Work"
            assert result_data["groups"][0]["by_folder"][0]["count"] == 15

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["aggregations"]["by_folder"]["group_by"] == "folderName"

    @pytest.mark.asyncio
    async def test_search_with_include_examples(self):
        """Test search with include_examples in aggregation."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "entity": "projects",
                "groupedBy": "folderName",
                "groups": [
                    {
                        "folderName": "Work",
                        "count": 8,
                        "examples": [
                            {"id": "proj1", "name": "Project 1", "dueDate": "2026-02-15"},
                            {"id": "proj2", "name": "Project 2", "dueDate": None},
                        ],
                    },
                ],
            }

            aggregations = {
                "count": "count",
                "examples": {
                    "include_examples": 2,
                    "example_fields": ["id", "name", "dueDate"],
                },
            }

            result = await search(
                entity="projects", group_by="folderName", aggregations=aggregations
            )
            result_data = json.loads(result)

            assert len(result_data["groups"][0]["examples"]) == 2
            assert result_data["groups"][0]["examples"][0]["name"] == "Project 1"

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["aggregations"]["examples"]["include_examples"] == 2

    @pytest.mark.asyncio
    async def test_search_backward_compatibility_no_group_by(self):
        """Test that search without group_by returns original format."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "count": 2,
                "entity": "tasks",
                "items": [
                    {"id": "task1", "name": "Task 1"},
                    {"id": "task2", "name": "Task 2"},
                ],
            }

            result = await search(entity="tasks")
            result_data = json.loads(result)

            # Should return original format (not grouped)
            assert "count" in result_data
            assert "items" in result_data
            assert "groups" not in result_data
            assert "groupedBy" not in result_data

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["group_by"] is None
            assert params["aggregations"] is None

    @pytest.mark.asyncio
    async def test_search_group_by_with_filters(self):
        """Test that group_by works alongside filters."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "entity": "projects",
                "groupedBy": "folderName",
                "groups": [{"folderName": "Work", "count": 5}],
            }

            await search(
                entity="projects",
                group_by="folderName",
                filters={"status": ["Active"]},
            )

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["group_by"] == "folderName"
            assert params["filters"]["status"] == ["Active"]

    @pytest.mark.asyncio
    async def test_search_multi_level_nested_aggregation(self):
        """Test search with complex multi-level nested aggregation."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "entity": "projects",
                "groupedBy": "status",
                "groups": [
                    {
                        "status": "Active",
                        "count": 23,
                        "by_folder": [
                            {
                                "folderName": "Work",
                                "count": 15,
                                "stuck_count": 3,
                                "goal_count": 0,
                            },
                            {
                                "folderName": "Goals",
                                "count": 8,
                                "stuck_count": 1,
                                "goal_count": 8,
                            },
                        ],
                    },
                ],
            }

            aggregations = {
                "count": "count",
                "by_folder": {
                    "group_by": "folderName",
                    "count": "count",
                    "stuck_count": {"filter": {"modified_before": 21}, "aggregate": "count"},
                    "goal_count": {
                        "filter": {"folder_name_contains": "Goals"},
                        "aggregate": "count",
                    },
                },
            }

            result = await search(entity="projects", group_by="status", aggregations=aggregations)
            result_data = json.loads(result)

            folder_groups = result_data["groups"][0]["by_folder"]
            assert folder_groups[0]["stuck_count"] == 3
            assert folder_groups[0]["goal_count"] == 0
            assert folder_groups[1]["stuck_count"] == 1
            assert folder_groups[1]["goal_count"] == 8
