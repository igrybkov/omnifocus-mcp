"""Tests for applescript_builder module."""

import pytest

from omnifocus_mcp.applescript_builder import (
    DateParams,
    generate_find_clause,
    generate_tag_modifications,
    process_date_params,
)


class TestDateParams:
    """Tests for DateParams class."""

    def test_empty_date_params(self):
        """Test DateParams with no scripts."""
        params = DateParams()
        assert params.pre_tell_scripts == []
        assert params.in_tell_assignments == []
        assert params.pre_tell_script == ""

    def test_pre_tell_script_joins_with_double_newline(self):
        """Test that pre_tell_script joins scripts with double newlines."""
        params = DateParams()
        params.pre_tell_scripts = ["script1", "script2"]
        assert params.pre_tell_script == "script1\n\nscript2"


class TestProcessDateParams:
    """Tests for process_date_params function."""

    def test_no_dates(self):
        """Test with no date parameters."""
        result = process_date_params("theTask")
        assert result.pre_tell_scripts == []
        assert result.in_tell_assignments == []

    def test_due_date_only(self):
        """Test with only due date."""
        result = process_date_params("theTask", due_date="2025-02-01")
        assert len(result.pre_tell_scripts) == 1
        assert len(result.in_tell_assignments) == 1
        assert "due date" in result.in_tell_assignments[0]
        assert "theTask" in result.in_tell_assignments[0]

    def test_defer_date_only(self):
        """Test with only defer date."""
        result = process_date_params("theTask", defer_date="2025-02-01")
        assert len(result.pre_tell_scripts) == 1
        assert len(result.in_tell_assignments) == 1
        assert "defer date" in result.in_tell_assignments[0]

    def test_planned_date_only(self):
        """Test with only planned date."""
        result = process_date_params("theTask", planned_date="2025-02-01")
        assert len(result.pre_tell_scripts) == 1
        assert len(result.in_tell_assignments) == 1
        assert "planned date" in result.in_tell_assignments[0]

    def test_all_dates(self):
        """Test with all three dates."""
        result = process_date_params(
            "theTask",
            due_date="2025-02-01",
            defer_date="2025-01-15",
            planned_date="2025-01-20",
        )
        assert len(result.pre_tell_scripts) == 3
        assert len(result.in_tell_assignments) == 3

    def test_include_planned_false(self):
        """Test that planned date is skipped when include_planned=False."""
        result = process_date_params(
            "theProject",
            due_date="2025-02-01",
            planned_date="2025-01-20",
            include_planned=False,
        )
        assert len(result.pre_tell_scripts) == 1
        assert len(result.in_tell_assignments) == 1
        assert "due date" in result.in_tell_assignments[0]
        # planned date should not be included
        assert not any("planned date" in a for a in result.in_tell_assignments)

    def test_clear_date_with_empty_string(self):
        """Test clearing a date with empty string."""
        result = process_date_params("theTask", due_date="")
        assert result.pre_tell_scripts == []  # No pre-script needed for clearing
        assert len(result.in_tell_assignments) == 1
        assert "missing value" in result.in_tell_assignments[0]

    def test_custom_object_var(self):
        """Test with custom object variable name."""
        result = process_date_params("myCustomTask", due_date="2025-02-01")
        assert "myCustomTask" in result.in_tell_assignments[0]


class TestGenerateFindClause:
    """Tests for generate_find_clause function."""

    def test_find_task_by_id(self):
        """Test finding a task by ID."""
        result = generate_find_clause("task", "theTask", item_id="abc123")
        assert 'set theTask to first flattened task where id = "abc123"' == result

    def test_find_task_by_name(self):
        """Test finding a task by name."""
        result = generate_find_clause("task", "theTask", item_name="My Task")
        assert 'set theTask to first flattened task where its name = "My Task"' == result

    def test_find_project_by_id(self):
        """Test finding a project by ID."""
        result = generate_find_clause("project", "theProject", item_id="xyz789")
        assert 'set theProject to first flattened project where id = "xyz789"' == result

    def test_find_project_by_name(self):
        """Test finding a project by name."""
        result = generate_find_clause("project", "theProject", item_name="My Project")
        assert 'set theProject to first flattened project where its name = "My Project"' == result

    def test_id_takes_precedence_over_name(self):
        """Test that ID takes precedence when both are provided."""
        result = generate_find_clause("task", "theTask", item_id="abc123", item_name="My Task")
        assert "abc123" in result
        assert "My Task" not in result

    def test_escapes_special_characters_in_id(self):
        """Test that special characters in ID are escaped."""
        result = generate_find_clause("task", "theTask", item_id='test"id')
        assert '\\"' in result

    def test_escapes_special_characters_in_name(self):
        """Test that special characters in name are escaped."""
        result = generate_find_clause("task", "theTask", item_name='Task "with" quotes')
        assert '\\"' in result

    def test_raises_error_when_neither_id_nor_name(self):
        """Test that ValueError is raised when neither ID nor name is provided."""
        with pytest.raises(ValueError, match="Either item_id or item_name must be provided"):
            generate_find_clause("task", "theTask")


class TestGenerateTagModifications:
    """Tests for generate_tag_modifications function."""

    def test_no_tags(self):
        """Test with no tag operations."""
        mods, changes = generate_tag_modifications("theTask")
        assert mods == []
        assert changes == []

    def test_add_tags(self):
        """Test adding tags."""
        mods, changes = generate_tag_modifications("theTask", add_tags=["tag1", "tag2"])
        assert len(mods) == 1
        assert changes == ["tags (added)"]
        assert "tag1" in mods[0]
        assert "tag2" in mods[0]

    def test_remove_tags(self):
        """Test removing tags."""
        mods, changes = generate_tag_modifications("theTask", remove_tags=["tag1"])
        assert len(mods) == 1
        assert changes == ["tags (removed)"]
        assert "remove" in mods[0].lower()

    def test_replace_tags(self):
        """Test replacing tags."""
        mods, changes = generate_tag_modifications("theTask", replace_tags=["new_tag"])
        assert len(mods) == 1
        assert changes == ["tags (replaced)"]

    def test_replace_takes_precedence(self):
        """Test that replace_tags takes precedence over add/remove."""
        mods, changes = generate_tag_modifications(
            "theTask",
            add_tags=["add_me"],
            remove_tags=["remove_me"],
            replace_tags=["replace_with"],
        )
        # Should only have replace operation
        assert len(mods) == 1
        assert changes == ["tags (replaced)"]
        assert "replace_with" in mods[0] or "existingTags" in mods[0]  # replace clears first

    def test_add_and_remove_together(self):
        """Test add and remove operations together (when no replace)."""
        mods, changes = generate_tag_modifications(
            "theTask", add_tags=["add_me"], remove_tags=["remove_me"]
        )
        assert len(mods) == 2
        assert "tags (added)" in changes
        assert "tags (removed)" in changes
