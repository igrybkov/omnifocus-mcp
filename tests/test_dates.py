"""Tests for date utilities including natural language parsing."""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from omnifocus_mcp.dates import parse_natural_date, preprocess_date_filters


class TestParseNaturalDate:
    """Tests for parse_natural_date function."""

    def test_parse_iso_date(self):
        """Test parsing ISO format date."""
        result = parse_natural_date("2024-01-25")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 25

    def test_parse_iso_datetime(self):
        """Test parsing ISO format datetime."""
        result = parse_natural_date("2024-01-25T14:30:00")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 25
        assert result.hour == 14
        assert result.minute == 30

    def test_parse_today(self):
        """Test parsing 'today'."""
        result = parse_natural_date("today")
        assert result is not None
        assert result.date() == date.today()

    def test_parse_tomorrow(self):
        """Test parsing 'tomorrow'."""
        result = parse_natural_date("tomorrow")
        assert result is not None
        expected = date.today() + timedelta(days=1)
        assert result.date() == expected

    def test_parse_yesterday(self):
        """Test parsing 'yesterday'."""
        result = parse_natural_date("yesterday")
        assert result is not None
        expected = date.today() - timedelta(days=1)
        assert result.date() == expected

    def test_parse_in_n_days(self):
        """Test parsing 'in 3 days'."""
        result = parse_natural_date("in 3 days")
        assert result is not None
        expected = date.today() + timedelta(days=3)
        assert result.date() == expected

    def test_parse_n_days_ago(self):
        """Test parsing '2 days ago'."""
        result = parse_natural_date("2 days ago")
        assert result is not None
        expected = date.today() - timedelta(days=2)
        assert result.date() == expected

    def test_parse_next_week(self):
        """Test parsing 'next week'."""
        result = parse_natural_date("next week")
        assert result is not None
        # Should be approximately 7 days from now
        assert result.date() >= date.today()

    def test_parse_invalid_returns_none(self):
        """Test that invalid input returns None."""
        assert parse_natural_date("not a date at all xyz") is None

    def test_parse_empty_string_returns_none(self):
        """Test that empty string returns None."""
        assert parse_natural_date("") is None

    def test_parse_none_returns_none(self):
        """Test that None returns None."""
        assert parse_natural_date(None) is None

    def test_parse_non_string_returns_none(self):
        """Test that non-string returns None."""
        assert parse_natural_date(123) is None


class TestPreprocessDateFilters:
    """Tests for preprocess_date_filters function."""

    def test_empty_filters(self):
        """Test with empty filters."""
        result = preprocess_date_filters({})
        assert result == {}

    def test_none_filters(self):
        """Test with None filters."""
        result = preprocess_date_filters(None)
        assert result is None

    def test_numeric_filter_unchanged(self):
        """Test that numeric filters pass through unchanged."""
        result = preprocess_date_filters({"due_within": 7})
        assert result["due_within"] == 7

    def test_non_date_filter_unchanged(self):
        """Test that non-date filters pass through unchanged."""
        filters = {"flagged": True, "tags": ["urgent"]}
        result = preprocess_date_filters(filters)
        assert result["flagged"] is True
        assert result["tags"] == ["urgent"]

    def test_tomorrow_converts_to_days(self):
        """Test 'tomorrow' converts to 1 day."""
        result = preprocess_date_filters({"due_within": "tomorrow"})
        assert result["due_within"] == 1

    def test_today_converts_to_zero(self):
        """Test 'today' converts to 0 days."""
        result = preprocess_date_filters({"due_within": "today"})
        assert result["due_within"] == 0

    def test_in_3_days_converts(self):
        """Test 'in 3 days' converts to 3."""
        result = preprocess_date_filters({"due_within": "in 3 days"})
        assert result["due_within"] == 3

    def test_all_days_filters_processed(self):
        """Test all date filters are processed."""
        filters = {
            "due_within": "tomorrow",
            "deferred_until": "in 2 days",
            "planned_within": "in 5 days",
        }
        result = preprocess_date_filters(filters)
        assert result["due_within"] == 1
        assert result["deferred_until"] == 2
        assert result["planned_within"] == 5

    def test_unparseable_filter_removed(self):
        """Test that unparseable string filters are removed."""
        result = preprocess_date_filters({"due_within": "not a valid date xyz"})
        assert "due_within" not in result

    def test_mixed_filters(self):
        """Test mix of date and non-date filters."""
        filters = {
            "flagged": True,
            "due_within": "tomorrow",
            "tags": ["work"],
        }
        result = preprocess_date_filters(filters)
        assert result["flagged"] is True
        assert result["due_within"] == 1
        assert result["tags"] == ["work"]

    def test_original_dict_not_modified(self):
        """Test that original dict is not modified."""
        original = {"due_within": "tomorrow"}
        preprocess_date_filters(original)
        assert original["due_within"] == "tomorrow"  # Still string

    def test_iso_date_converts_to_days(self):
        """Test ISO date converts to days from today."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        result = preprocess_date_filters({"due_within": tomorrow})
        assert result["due_within"] == 1


class TestSearchWithNaturalLanguage:
    """Tests for search tool with natural language dates."""

    @pytest.mark.asyncio
    async def test_search_with_natural_language_due_within(self):
        """Test search tool converts natural language due_within."""
        from omnifocus_mcp.mcp_tools.query.search import search

        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", filters={"due_within": "tomorrow"})

            script_name, params, *_ = mock_exec.call_args[0]
            # Should be converted to numeric days
            assert params["filters"]["due_within"] == 1

    @pytest.mark.asyncio
    async def test_search_with_numeric_due_within_unchanged(self):
        """Test search tool passes numeric due_within unchanged."""
        from omnifocus_mcp.mcp_tools.query.search import search

        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(entity="tasks", filters={"due_within": 7})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["due_within"] == 7

    @pytest.mark.asyncio
    async def test_search_with_natural_language_multiple_filters(self):
        """Test search tool converts multiple natural language date filters."""
        from omnifocus_mcp.mcp_tools.query.search import search

        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"count": 0, "entity": "tasks", "items": []}

            await search(
                entity="tasks",
                filters={
                    "due_within": "in 3 days",
                    "planned_within": "next week",
                },
            )

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["due_within"] == 3
            # next week should be >= 7 days
            assert params["filters"]["planned_within"] >= 7


class TestBrowseWithNaturalLanguage:
    """Tests for browse tool with natural language dates."""

    @pytest.mark.asyncio
    async def test_browse_with_natural_language_project_filter(self):
        """Test browse tool converts natural language in project filters."""
        from omnifocus_mcp.mcp_tools.projects.browse import browse

        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"tree": [], "projectCount": 0, "folderCount": 0}

            await browse(filters={"due_within": "tomorrow"})

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["filters"]["due_within"] == 1

    @pytest.mark.asyncio
    async def test_browse_with_natural_language_task_filter(self):
        """Test browse tool converts natural language in task filters."""
        from omnifocus_mcp.mcp_tools.projects.browse import browse

        with patch("omnifocus_mcp.mcp_tools.response.execute_omnijs_with_params") as mock_exec:
            mock_exec.return_value = {"tree": [], "projectCount": 0, "folderCount": 0}

            await browse(
                include_tasks=True,
                task_filters={"planned_within": "in 2 days"},
            )

            script_name, params, *_ = mock_exec.call_args[0]
            assert params["task_filters"]["planned_within"] == 2
