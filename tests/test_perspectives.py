"""Tests for perspective tools - list, view, and rules."""

import json
from unittest.mock import patch

import pytest

from omnifocus_mcp.mcp_tools.perspectives.get_perspective_rules import (
    get_perspective_rules,
)
from omnifocus_mcp.mcp_tools.perspectives.get_perspective_view import (
    get_perspective_view,
)
from omnifocus_mcp.mcp_tools.perspectives.list_perspectives import list_perspectives


class TestListPerspectives:
    """Tests for list_perspectives function."""

    @pytest.mark.asyncio
    async def test_list_perspectives_basic(self):
        """Test basic perspective listing."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "total": 8,
                "builtInCount": 6,
                "customCount": 2,
                "perspectives": [
                    {"id": "builtin_inbox", "name": "Inbox", "type": "builtin"},
                    {"id": "custom_1", "name": "Today", "type": "custom"},
                ],
            }

            result = await list_perspectives()
            result_data = json.loads(result)

            assert result_data["total"] == 8
            assert result_data["builtInCount"] == 6
            assert result_data["customCount"] == 2
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_perspectives_exclude_builtin(self):
        """Test listing only custom perspectives."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"total": 2, "perspectives": []}

            await list_perspectives(include_built_in=False)

            script_name, params = mock_exec.call_args[0]
            assert params["include_built_in"] is False
            assert params["include_custom"] is True

    @pytest.mark.asyncio
    async def test_list_perspectives_exclude_custom(self):
        """Test listing only built-in perspectives."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"total": 6, "perspectives": []}

            await list_perspectives(include_custom=False)

            script_name, params = mock_exec.call_args[0]
            assert params["include_built_in"] is True
            assert params["include_custom"] is False


class TestGetPerspectiveView:
    """Tests for get_perspective_view function."""

    @pytest.mark.asyncio
    async def test_get_perspective_view_basic(self):
        """Test basic perspective view."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "perspectiveName": "Flagged",
                "type": "builtin",
                "count": 3,
                "items": [
                    {"id": "task1", "name": "Task 1", "flagged": True},
                ],
            }

            result = await get_perspective_view("Flagged")
            result_data = json.loads(result)

            assert result_data["perspectiveName"] == "Flagged"
            assert result_data["count"] == 3

    @pytest.mark.asyncio
    async def test_get_perspective_view_with_limit(self):
        """Test perspective view with limit."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"perspectiveName": "Inbox", "count": 10, "items": []}

            await get_perspective_view("Inbox", limit=10)

            script_name, params = mock_exec.call_args[0]
            assert params["limit"] == 10

    @pytest.mark.asyncio
    async def test_get_perspective_view_with_fields(self):
        """Test perspective view with specific fields."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"perspectiveName": "Inbox", "count": 0, "items": []}

            await get_perspective_view("Inbox", fields=["id", "name", "dueDate"])

            script_name, params = mock_exec.call_args[0]
            assert params["fields"] == ["id", "name", "dueDate"]


class TestGetPerspectiveRules:
    """Tests for get_perspective_rules function."""

    @pytest.mark.asyncio
    async def test_get_perspective_rules_basic(self):
        """Test basic perspective rules retrieval."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "perspectiveName": "Today",
                "perspectiveId": "abc123",
                "aggregation": "all",
                "aggregationDescription": "Match ALL of the following rules",
                "ruleCount": 2,
                "rules": [
                    {"actionAvailability": "remaining"},
                    {"actionHasAnyOfTags": ["Work", "Urgent"]},
                ],
            }

            result = await get_perspective_rules("Today")
            result_data = json.loads(result)

            assert result_data["perspectiveName"] == "Today"
            assert result_data["aggregation"] == "all"
            assert result_data["ruleCount"] == 2
            assert len(result_data["rules"]) == 2
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_perspective_rules_case_insensitive(self):
        """Test that perspective name lookup is case-insensitive."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "perspectiveName": "Today",
                "aggregation": "all",
                "ruleCount": 1,
                "rules": [],
            }

            await get_perspective_rules("TODAY")

            script_name, params = mock_exec.call_args[0]
            assert params["perspective_name"] == "TODAY"

    @pytest.mark.asyncio
    async def test_get_perspective_rules_resolve_ids_true(self):
        """Test that resolve_ids defaults to True."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "perspectiveName": "Today",
                "aggregation": "all",
                "ruleCount": 1,
                "rules": [
                    {
                        "actionHasAnyOfTags": ["Work", "Urgent"],
                        "_originalTagIds": ["tag1", "tag2"],
                    }
                ],
            }

            result = await get_perspective_rules("Today")
            result_data = json.loads(result)

            # With resolve_ids=True, tags should be names
            assert result_data["rules"][0]["actionHasAnyOfTags"] == ["Work", "Urgent"]
            assert result_data["rules"][0]["_originalTagIds"] == ["tag1", "tag2"]

            script_name, params = mock_exec.call_args[0]
            assert params["resolve_ids"] is True

    @pytest.mark.asyncio
    async def test_get_perspective_rules_resolve_ids_false(self):
        """Test with resolve_ids=False to get raw IDs."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "perspectiveName": "Today",
                "aggregation": "all",
                "ruleCount": 1,
                "rules": [{"actionHasAnyOfTags": ["tag1", "tag2"]}],
            }

            await get_perspective_rules("Today", resolve_ids=False)

            script_name, params = mock_exec.call_args[0]
            assert params["resolve_ids"] is False

    @pytest.mark.asyncio
    async def test_get_perspective_rules_not_found(self):
        """Test error when perspective not found."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "error": "Perspective not found: NonExistent",
                "availablePerspectives": ["Today", "Next", "Waiting"],
            }

            result = await get_perspective_rules("NonExistent")
            result_data = json.loads(result)

            assert "error" in result_data
            assert "NonExistent" in result_data["error"]
            assert "availablePerspectives" in result_data

    @pytest.mark.asyncio
    async def test_get_perspective_rules_with_nested_rules(self):
        """Test perspective with nested aggregate rules."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "perspectiveName": "Complex",
                "aggregation": "all",
                "ruleCount": 2,
                "rules": [
                    {"actionAvailability": "available"},
                    {
                        "aggregateRules": [
                            {"actionStatus": "flagged"},
                            {"actionStatus": "due"},
                        ],
                        "aggregateType": "any",
                    },
                ],
            }

            result = await get_perspective_rules("Complex")
            result_data = json.loads(result)

            assert result_data["ruleCount"] == 2
            nested_rule = result_data["rules"][1]
            assert "aggregateRules" in nested_rule
            assert nested_rule["aggregateType"] == "any"

    @pytest.mark.asyncio
    async def test_get_perspective_rules_with_disabled_rules(self):
        """Test perspective with disabled rules."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "perspectiveName": "Test",
                "aggregation": "all",
                "ruleCount": 1,
                "rules": [
                    {
                        "disabledRule": {"actionIsProjectOrGroup": True},
                    }
                ],
            }

            result = await get_perspective_rules("Test")
            result_data = json.loads(result)

            assert "disabledRule" in result_data["rules"][0]

    @pytest.mark.asyncio
    async def test_get_perspective_rules_uses_correct_script(self):
        """Test that the correct script name is used."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {
                "perspectiveName": "Test",
                "aggregation": "all",
                "ruleCount": 0,
                "rules": [],
            }

            await get_perspective_rules("Test")

            script_name, params = mock_exec.call_args[0]
            assert script_name == "get_perspective_rules"

    @pytest.mark.asyncio
    async def test_get_perspective_rules_exception_handling(self):
        """Test exception handling."""
        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.side_effect = Exception("Test exception")

            result = await get_perspective_rules("Test")
            result_data = json.loads(result)

            assert "error" in result_data
            assert "Test exception" in result_data["error"]
