"""Tests for get_tree tool - hierarchical view of folders, projects, and tasks."""

import json
import pytest
from unittest.mock import AsyncMock, patch
from omnifocus_mcp.mcp_tools.projects.tree import get_tree


class TestGetTree:
    """Tests for get_tree function."""

    @pytest.mark.asyncio
    async def test_get_tree_basic(self):
        """Test basic project tree retrieval."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
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
                                "tagNames": []
                            }
                        ]
                    }
                ],
                "projectCount": 1,
                "folderCount": 1
            }

            result = await get_tree()
            result_data = json.loads(result)

            assert "tree" in result_data
            assert result_data["projectCount"] == 1
            assert result_data["folderCount"] == 1
            assert result_data["tree"][0]["type"] == "folder"
            assert result_data["tree"][0]["name"] == "Work"
            assert len(result_data["tree"][0]["children"]) == 1
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tree_with_parent_id(self):
        """Test project tree with parent_id filter."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [
                    {
                        "type": "folder",
                        "id": "folder1",
                        "name": "Work",
                        "children": []
                    }
                ],
                "projectCount": 0,
                "folderCount": 1
            }

            result = await get_tree(parent_id="folder1")

            # Verify the script contains the parent_id filter
            call_args = mock_exec.call_args[0][0]
            assert 'folder1' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_with_parent_name(self):
        """Test project tree with parent_name filter."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [
                    {
                        "type": "folder",
                        "id": "folder1",
                        "name": "Work",
                        "children": []
                    }
                ],
                "projectCount": 0,
                "folderCount": 1
            }

            result = await get_tree(parent_name="Work")

            # Verify the script contains the parent_name filter
            call_args = mock_exec.call_args[0][0]
            assert 'work' in call_args.lower()

    @pytest.mark.asyncio
    async def test_get_tree_with_status_filter(self):
        """Test project tree with status filter."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [],
                "projectCount": 0,
                "folderCount": 0
            }

            result = await get_tree(filters={"status": ["Active", "OnHold"]})

            # Verify the script contains status filter logic
            call_args = mock_exec.call_args[0][0]
            assert 'Active' in call_args
            assert 'OnHold' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_with_flagged_filter(self):
        """Test project tree with flagged filter."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [],
                "projectCount": 0,
                "folderCount": 0
            }

            result = await get_tree(filters={"flagged": True})

            # Verify the script contains flagged filter logic
            call_args = mock_exec.call_args[0][0]
            assert 'project.flagged !== true' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_with_tags_filter(self):
        """Test project tree with tags filter."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [],
                "projectCount": 0,
                "folderCount": 0
            }

            result = await get_tree(filters={"tags": ["work", "important"]})

            # Verify the script contains tags filter logic
            call_args = mock_exec.call_args[0][0]
            assert 'work' in call_args
            assert 'important' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_include_completed(self):
        """Test project tree with include_completed=True."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [],
                "projectCount": 0,
                "folderCount": 0
            }

            result = await get_tree(include_completed=True)

            # When include_completed=True, the completed filter should not be in script
            call_args = mock_exec.call_args[0][0]
            # The completed filter checks for Project.Status.Done
            assert 'Project.Status.Done' not in call_args or 'return false' not in call_args.split('Project.Status.Done')[1][:50]

    @pytest.mark.asyncio
    async def test_get_tree_with_max_depth(self):
        """Test project tree with max_depth limit."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [],
                "projectCount": 0,
                "folderCount": 0
            }

            result = await get_tree(max_depth=2)

            # Verify the script contains max_depth setting
            call_args = mock_exec.call_args[0][0]
            assert 'const maxDepth = 2' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_error_handling(self):
        """Test error handling when OmniJS returns an error."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {"error": "Folder not found with ID: invalid_id"}

            result = await get_tree(parent_id="invalid_id")
            result_data = json.loads(result)

            assert "error" in result_data
            assert "Folder not found" in result_data["error"]

    @pytest.mark.asyncio
    async def test_get_tree_exception_handling(self):
        """Test exception handling."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.side_effect = Exception("Test exception")

            result = await get_tree()
            result_data = json.loads(result)

            assert "error" in result_data
            assert "Test exception" in result_data["error"]

    @pytest.mark.asyncio
    async def test_get_tree_nested_folders(self):
        """Test project tree with nested folder structure."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
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
                                        "tagNames": []
                                    }
                                ]
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
                                "tagNames": ["important"]
                            }
                        ]
                    }
                ],
                "projectCount": 2,
                "folderCount": 2
            }

            result = await get_tree()
            result_data = json.loads(result)

            assert result_data["projectCount"] == 2
            assert result_data["folderCount"] == 2

            # Check nested structure
            work_folder = result_data["tree"][0]
            assert work_folder["name"] == "Work"
            assert len(work_folder["children"]) == 2

            # Find the Projects subfolder
            projects_folder = next(
                (c for c in work_folder["children"] if c["type"] == "folder"),
                None
            )
            assert projects_folder is not None
            assert projects_folder["name"] == "Projects"
            assert len(projects_folder["children"]) == 1

    @pytest.mark.asyncio
    async def test_get_tree_with_due_within_filter(self):
        """Test project tree with due_within filter."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [],
                "projectCount": 0,
                "folderCount": 0
            }

            result = await get_tree(filters={"due_within": 7})

            call_args = mock_exec.call_args[0][0]
            assert 'project.dueDate' in call_args
            assert '7' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_exclude_root_projects(self):
        """Test project tree with include_root_projects=False."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [],
                "projectCount": 0,
                "folderCount": 0
            }

            result = await get_tree(include_root_projects=False)

            call_args = mock_exec.call_args[0][0]
            assert 'includeRootProjects = false' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_summary_mode(self):
        """Test project tree with summary=True returns only counts."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "projectCount": 37,
                "folderCount": 6
            }

            result = await get_tree(summary=True)
            result_data = json.loads(result)

            # Summary mode should not include tree
            assert "tree" not in result_data
            assert result_data["projectCount"] == 37
            assert result_data["folderCount"] == 6

            # Verify script has summaryOnly set to true
            call_args = mock_exec.call_args[0][0]
            assert 'summaryOnly = true' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_summary_mode_with_filters(self):
        """Test summary mode works with filters."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "projectCount": 10,
                "folderCount": 3
            }

            result = await get_tree(
                summary=True,
                filters={"status": ["Active"]},
                parent_name="Goals"
            )
            result_data = json.loads(result)

            assert "tree" not in result_data
            assert result_data["projectCount"] == 10

    @pytest.mark.asyncio
    async def test_get_tree_with_fields_filter(self):
        """Test project tree with specific fields requested."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
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
                                "name": "Project A"
                            }
                        ]
                    }
                ],
                "projectCount": 1,
                "folderCount": 1
            }

            result = await get_tree(fields=["id", "name"])

            # Verify script has requested fields
            call_args = mock_exec.call_args[0][0]
            assert 'requestedFields = ["id", "name"]' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_fields_always_includes_type(self):
        """Test that project type is always included regardless of fields."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [
                    {
                        "type": "folder",
                        "id": "folder1",
                        "name": "Work",
                        "children": [
                            {
                                "type": "project",
                                "name": "Project A"
                            }
                        ]
                    }
                ],
                "projectCount": 1,
                "folderCount": 1
            }

            result = await get_tree(fields=["name"])
            result_data = json.loads(result)

            # Even with only 'name' requested, type should be included
            project = result_data["tree"][0]["children"][0]
            assert project["type"] == "project"

    @pytest.mark.asyncio
    async def test_get_tree_empty_fields_returns_all(self):
        """Test that empty fields list returns all fields."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [],
                "projectCount": 0,
                "folderCount": 0
            }

            result = await get_tree(fields=[])

            # Verify script has empty requestedFields (returns all)
            call_args = mock_exec.call_args[0][0]
            assert 'requestedFields = []' in call_args
            assert 'if (requestedFields.length === 0)' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_uses_parent_for_root_folders(self):
        """Test that root folders are identified using .parent property."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [],
                "projectCount": 0,
                "folderCount": 0
            }

            result = await get_tree()

            # Verify script uses .parent for folders (not .folder)
            call_args = mock_exec.call_args[0][0]
            assert 'flattenedFolders.filter(f => !f.parent)' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_parent_name_partial_match_single(self):
        """Test partial parent name match when single result found."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [
                    {
                        "type": "folder",
                        "id": "folder1",
                        "name": "🎯 Goals",
                        "children": []
                    }
                ],
                "projectCount": 0,
                "folderCount": 1
            }

            # Search for "Goals" should match "🎯 Goals"
            result = await get_tree(parent_name="Goals")

            # Verify script has partial match logic
            call_args = mock_exec.call_args[0][0]
            assert 'includes("goals")' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_parent_name_partial_match_suggestions(self):
        """Test partial parent name match returns suggestions when multiple found."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "error": "Folder not found with name: Work",
                "suggestions": [
                    {"id": "folder1", "name": "🏢 Work"},
                    {"id": "folder2", "name": "Work Projects"}
                ]
            }

            result = await get_tree(parent_name="Work")
            result_data = json.loads(result)

            assert "error" in result_data
            assert "suggestions" in result_data
            assert len(result_data["suggestions"]) == 2

    @pytest.mark.asyncio
    async def test_get_tree_parent_name_no_match(self):
        """Test parent name with no matches returns error without suggestions."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "error": "Folder not found with name: NonExistent"
            }

            result = await get_tree(parent_name="NonExistent")
            result_data = json.loads(result)

            assert "error" in result_data
            assert "suggestions" not in result_data

    @pytest.mark.asyncio
    async def test_get_tree_include_folders_false(self):
        """Test include_folders=False returns flat list of projects."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [
                    {"type": "project", "id": "proj1", "name": "Project A"},
                    {"type": "project", "id": "proj2", "name": "Project B"}
                ],
                "projectCount": 2,
                "folderCount": 1
            }

            result = await get_tree(include_folders=False)

            # Verify script has includeFolders = false
            call_args = mock_exec.call_args[0][0]
            assert 'includeFolders = false' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_include_projects_false(self):
        """Test include_projects=False returns only folder structure."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "tree": [
                    {
                        "type": "folder",
                        "id": "folder1",
                        "name": "Work",
                        "children": []
                    }
                ],
                "projectCount": 0,
                "folderCount": 1
            }

            result = await get_tree(include_projects=False)

            # Verify script has includeProjects = false
            call_args = mock_exec.call_args[0][0]
            assert 'includeProjects = false' in call_args

    @pytest.mark.asyncio
    async def test_get_tree_include_tasks_true(self):
        """Test include_tasks=True returns tasks within projects."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
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
                                    {"type": "task", "id": "task2", "name": "Task 2"}
                                ]
                            }
                        ]
                    }
                ],
                "projectCount": 1,
                "folderCount": 1,
                "taskCount": 2
            }

            result = await get_tree(include_tasks=True)
            result_data = json.loads(result)

            # Verify script has includeTasks = true
            call_args = mock_exec.call_args[0][0]
            assert 'includeTasks = true' in call_args

            # Verify taskCount is in response
            assert result_data["taskCount"] == 2

    @pytest.mark.asyncio
    async def test_get_tree_summary_with_tasks(self):
        """Test summary mode with include_tasks returns taskCount."""
        with patch('omnifocus_mcp.mcp_tools.projects.tree.execute_omnijs') as mock_exec:
            mock_exec.return_value = {
                "projectCount": 5,
                "folderCount": 2,
                "taskCount": 42
            }

            result = await get_tree(summary=True, include_tasks=True)
            result_data = json.loads(result)

            assert "tree" not in result_data
            assert result_data["projectCount"] == 5
            assert result_data["folderCount"] == 2
            assert result_data["taskCount"] == 42
