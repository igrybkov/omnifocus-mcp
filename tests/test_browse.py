"""Tests for browse tool - hierarchical view of folders, projects, and tasks."""

import json
from unittest.mock import patch

import pytest

from omnifocus_mcp.mcp_tools.projects.browse import browse


class TestBrowse:
    """Tests for browse function."""

    @pytest.mark.asyncio
    async def test_browse_basic(self):
        """Test basic project tree retrieval."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {
                "tree": [
                    {
                        "type": "folder",
                        "id": "folder1",
                        "name": "Work",
                        "children": [
                            {
                                "type": "project",
                                "id": "proj1",
                                "name": "Project A",
                                "status": "Active",
                                "sequential": False,
                                "flagged": False,
                                "dueDate": None,
                                "deferDate": None,
                                "estimatedMinutes": None,
                                "taskCount": 5,
                                "tagNames": [],
                            }
                        ],
                    }
                ],
                "projectCount": 1,
                "folderCount": 1,
            }

            result = await browse()
            result_data = json.loads(result)

            assert "tree" in result_data
            assert result_data["projectCount"] == 1
            assert result_data["folderCount"] == 1
            assert result_data["tree"][0]["type"] == "folder"
            assert result_data["tree"][0]["name"] == "Work"
            assert len(result_data["tree"][0]["children"]) == 1
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_browse_with_parent_id(self):
        """Test project tree with parent_id filter."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {
                "tree": [{"type": "folder", "id": "folder1", "name": "Work", "children": []}],
                "projectCount": 0,
                "folderCount": 1,
            }

            await browse(parent_id="folder1")

            script_name, params, *_ = mock_exec.call_args[0]
            assert script_name == "browse"
            assert params["parent_id"] == "folder1"

    @pytest.mark.asyncio
    async def test_browse_with_parent_name(self):
        """Test project tree with parent_name filter."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {
                "tree": [{"type": "folder", "id": "folder1", "name": "Work", "children": []}],
                "projectCount": 0,
                "folderCount": 1,
            }

            await browse(parent_name="Work")

            script_name, params, *_ = mock_exec.call_args[0]
            assert script_name == "browse"
            assert params["parent_name"] == "Work"

    @pytest.mark.asyncio
    async def test_browse_with_status_filter(self):
        """Test project tree with status filter."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"tree": [], "projectCount": 0, "folderCount": 0}

            await browse(filters={"status": ["Active", "OnHold"]})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["status"] == ["Active", "OnHold"]

    @pytest.mark.asyncio
    async def test_browse_with_flagged_filter(self):
        """Test project tree with flagged filter."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"tree": [], "projectCount": 0, "folderCount": 0}

            await browse(filters={"flagged": True})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["flagged"] is True

    @pytest.mark.asyncio
    async def test_browse_with_tags_filter(self):
        """Test project tree with tags filter."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"tree": [], "projectCount": 0, "folderCount": 0}

            await browse(filters={"tags": ["work", "important"]})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["tags"] == ["work", "important"]

    @pytest.mark.asyncio
    async def test_browse_include_completed(self):
        """Test project tree with include_completed=True."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"tree": [], "projectCount": 0, "folderCount": 0}

            await browse(include_completed=True)

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["include_completed"] is True

    @pytest.mark.asyncio
    async def test_browse_with_max_depth(self):
        """Test project tree with max_depth limit."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"tree": [], "projectCount": 0, "folderCount": 0}

            await browse(max_depth=2)

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["max_depth"] == 2

    @pytest.mark.asyncio
    async def test_browse_error_handling(self):
        """Test error handling when OmniJS returns an error."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"error": "Folder not found with ID: invalid_id"}

            result = await browse(parent_id="invalid_id")
            result_data = json.loads(result)

            assert "error" in result_data
            assert "Folder not found" in result_data["error"]

    @pytest.mark.asyncio
    async def test_browse_exception_handling(self):
        """Test exception handling."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.side_effect = Exception("Test exception")

            result = await browse()
            result_data = json.loads(result)

            assert "error" in result_data
            assert "Test exception" in result_data["error"]

    @pytest.mark.asyncio
    async def test_browse_nested_folders(self):
        """Test project tree with nested folder structure."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {
                "tree": [
                    {
                        "type": "folder",
                        "id": "folder1",
                        "name": "Work",
                        "children": [
                            {
                                "type": "folder",
                                "id": "folder2",
                                "name": "Projects",
                                "children": [
                                    {
                                        "type": "project",
                                        "id": "proj1",
                                        "name": "Project A",
                                        "status": "Active",
                                        "sequential": False,
                                        "flagged": False,
                                        "dueDate": None,
                                        "deferDate": None,
                                        "estimatedMinutes": None,
                                        "taskCount": 3,
                                        "tagNames": [],
                                    }
                                ],
                            },
                            {
                                "type": "project",
                                "id": "proj2",
                                "name": "Project B",
                                "status": "Active",
                                "sequential": True,
                                "flagged": True,
                                "dueDate": "2024-12-31T00:00:00.000Z",
                                "deferDate": None,
                                "estimatedMinutes": 60,
                                "taskCount": 10,
                                "tagNames": ["important"],
                            },
                        ],
                    }
                ],
                "projectCount": 2,
                "folderCount": 2,
            }

            result = await browse()
            result_data = json.loads(result)

            assert result_data["projectCount"] == 2
            assert result_data["folderCount"] == 2

            work_folder = result_data["tree"][0]
            assert work_folder["name"] == "Work"
            assert len(work_folder["children"]) == 2

            projects_folder = next(
                (c for c in work_folder["children"] if c["type"] == "folder"), None
            )
            assert projects_folder is not None
            assert projects_folder["name"] == "Projects"
            assert len(projects_folder["children"]) == 1

    @pytest.mark.asyncio
    async def test_browse_with_due_within_filter(self):
        """Test project tree with due_within filter."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"tree": [], "projectCount": 0, "folderCount": 0}

            await browse(filters={"due_within": 7})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["due_within"] == 7

    @pytest.mark.asyncio
    async def test_browse_exclude_root_projects(self):
        """Test project tree with include_root_projects=False."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"tree": [], "projectCount": 0, "folderCount": 0}

            await browse(include_root_projects=False)

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["include_root_projects"] is False

    @pytest.mark.asyncio
    async def test_browse_summary_mode(self):
        """Test project tree with summary=True returns only counts."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"projectCount": 37, "folderCount": 6}

            result = await browse(summary=True)
            result_data = json.loads(result)

            assert "tree" not in result_data
            assert result_data["projectCount"] == 37
            assert result_data["folderCount"] == 6

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["summary"] is True

    @pytest.mark.asyncio
    async def test_browse_summary_mode_with_filters(self):
        """Test summary mode works with filters."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"projectCount": 10, "folderCount": 3}

            result = await browse(summary=True, filters={"status": ["Active"]}, parent_name="Goals")
            result_data = json.loads(result)

            assert "tree" not in result_data
            assert result_data["projectCount"] == 10

    @pytest.mark.asyncio
    async def test_browse_with_fields_filter(self):
        """Test project tree with specific fields requested."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {
                "tree": [
                    {
                        "type": "folder",
                        "id": "folder1",
                        "name": "Work",
                        "children": [{"type": "project", "id": "proj1", "name": "Project A"}],
                    }
                ],
                "projectCount": 1,
                "folderCount": 1,
            }

            await browse(fields=["id", "name"])

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["fields"] == ["id", "name"]

    @pytest.mark.asyncio
    async def test_browse_fields_always_includes_type(self):
        """Test that project type is always included regardless of fields."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {
                "tree": [
                    {
                        "type": "folder",
                        "id": "folder1",
                        "name": "Work",
                        "children": [{"type": "project", "name": "Project A"}],
                    }
                ],
                "projectCount": 1,
                "folderCount": 1,
            }

            result = await browse(fields=["name"])
            result_data = json.loads(result)

            project = result_data["tree"][0]["children"][0]
            assert project["type"] == "project"

    @pytest.mark.asyncio
    async def test_browse_empty_fields_returns_all(self):
        """Test that empty fields list returns all fields."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"tree": [], "projectCount": 0, "folderCount": 0}

            await browse(fields=[])

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["fields"] == []

    @pytest.mark.asyncio
    async def test_browse_uses_correct_script_name(self):
        """Test that the correct script name is used."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"tree": [], "projectCount": 0, "folderCount": 0}

            await browse()

            script_name, params, *_ = mock_exec.call_args[0]
            assert script_name == "browse"

    @pytest.mark.asyncio
    async def test_browse_parent_name_partial_match_single(self):
        """Test partial parent name match when single result found."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {
                "tree": [{"type": "folder", "id": "folder1", "name": "🎯 Goals", "children": []}],
                "projectCount": 0,
                "folderCount": 1,
            }

            await browse(parent_name="Goals")

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["parent_name"] == "Goals"

    @pytest.mark.asyncio
    async def test_browse_parent_name_partial_match_suggestions(self):
        """Test partial parent name match returns suggestions when multiple found."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {
                "error": "Folder not found with name: Work",
                "suggestions": [
                    {"id": "folder1", "name": "🏢 Work"},
                    {"id": "folder2", "name": "Work Projects"},
                ],
            }

            result = await browse(parent_name="Work")
            result_data = json.loads(result)

            assert "error" in result_data
            assert "suggestions" in result_data
            assert len(result_data["suggestions"]) == 2

    @pytest.mark.asyncio
    async def test_browse_parent_name_no_match(self):
        """Test parent name with no matches returns error without suggestions."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"error": "Folder not found with name: NonExistent"}

            result = await browse(parent_name="NonExistent")
            result_data = json.loads(result)

            assert "error" in result_data
            assert "suggestions" not in result_data

    @pytest.mark.asyncio
    async def test_browse_include_folders_false(self):
        """Test include_folders=False returns flat list of projects."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {
                "tree": [
                    {"type": "project", "id": "proj1", "name": "Project A"},
                    {"type": "project", "id": "proj2", "name": "Project B"},
                ],
                "projectCount": 2,
                "folderCount": 1,
            }

            await browse(include_folders=False)

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["include_folders"] is False

    @pytest.mark.asyncio
    async def test_browse_include_projects_false(self):
        """Test include_projects=False returns only folder structure."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {
                "tree": [{"type": "folder", "id": "folder1", "name": "Work", "children": []}],
                "projectCount": 0,
                "folderCount": 1,
            }

            await browse(include_projects=False)

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["include_projects"] is False

    @pytest.mark.asyncio
    async def test_browse_include_tasks_true(self):
        """Test include_tasks=True returns tasks within projects."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {
                "tree": [
                    {
                        "type": "folder",
                        "id": "folder1",
                        "name": "Work",
                        "children": [
                            {
                                "type": "project",
                                "id": "proj1",
                                "name": "Project A",
                                "tasks": [
                                    {"type": "task", "id": "task1", "name": "Task 1"},
                                    {"type": "task", "id": "task2", "name": "Task 2"},
                                ],
                            }
                        ],
                    }
                ],
                "projectCount": 1,
                "folderCount": 1,
                "taskCount": 2,
            }

            result = await browse(include_tasks=True)
            result_data = json.loads(result)

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["include_tasks"] is True
            assert result_data["taskCount"] == 2

    @pytest.mark.asyncio
    async def test_browse_summary_with_tasks(self):
        """Test summary mode with include_tasks returns taskCount."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"projectCount": 5, "folderCount": 2, "taskCount": 42}

            result = await browse(summary=True, include_tasks=True)
            result_data = json.loads(result)

            assert "tree" not in result_data
            assert result_data["projectCount"] == 5
            assert result_data["folderCount"] == 2
            assert result_data["taskCount"] == 42

    @pytest.mark.asyncio
    async def test_browse_with_task_filters(self):
        """Test browse with task_filters parameter."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {
                "tree": [],
                "projectCount": 0,
                "folderCount": 0,
                "taskCount": 0,
            }

            await browse(include_tasks=True, task_filters={"flagged": True, "tags": ["urgent"]})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["task_filters"]["flagged"] is True
            assert params["task_filters"]["tags"] == ["urgent"]

    @pytest.mark.asyncio
    async def test_browse_with_available_filter(self):
        """Test browse with available filter for projects."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"tree": [], "projectCount": 0, "folderCount": 0}

            await browse(filters={"available": True})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["available"] is True

    @pytest.mark.asyncio
    async def test_browse_passes_includes(self):
        """Test that browse passes the includes parameter."""
        with patch(
            "omnifocus_mcp.mcp_tools.projects.browse.execute_omnijs_with_params"
        ) as mock_exec:
            mock_exec.return_value = {"tree": [], "projectCount": 0, "folderCount": 0}

            await browse()

            # Check that includes kwarg was passed
            call_kwargs = mock_exec.call_args[1]
            assert "includes" in call_kwargs
            assert "common/status_maps" in call_kwargs["includes"]
            assert "common/filters" in call_kwargs["includes"]
            assert "common/field_mappers" in call_kwargs["includes"]
