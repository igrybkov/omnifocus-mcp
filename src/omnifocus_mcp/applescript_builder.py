"""AppleScript builder utilities for common OmniFocus patterns.

This module provides helper functions to reduce duplicate code when building
AppleScript commands for OmniFocus operations.
"""

from .dates import create_date_assignment
from .tags import (
    generate_add_tags_applescript,
    generate_remove_tags_applescript,
    generate_replace_tags_applescript,
)
from .utils import escape_applescript_string


class DateParams:
    """Result of processing date parameters for AppleScript."""

    def __init__(self) -> None:
        self.pre_tell_scripts: list[str] = []
        self.in_tell_assignments: list[str] = []

    @property
    def pre_tell_script(self) -> str:
        """Get the combined pre-tell script for date variable creation."""
        return "\n\n".join(self.pre_tell_scripts) if self.pre_tell_scripts else ""

    def has_date(self, property_name: str) -> bool:
        """Check if a specific date property was processed."""
        return any(f"set {property_name} of" in a for a in self.in_tell_assignments)


def process_date_params(
    object_var: str,
    due_date: str | None = None,
    defer_date: str | None = None,
    planned_date: str | None = None,
    include_planned: bool = True,
) -> DateParams:
    """
    Process date parameters and generate AppleScript code.

    Handles the common pattern of creating date variables outside the tell block
    and assignments inside the tell block.

    Args:
        object_var: Name of the AppleScript variable for the object being modified
        due_date: Due date in ISO format, empty string to clear, or None to skip
        defer_date: Defer date in ISO format, empty string to clear, or None to skip
        planned_date: Planned date in ISO format, empty string to clear, or None to skip
        include_planned: Whether to process planned_date (False for projects)

    Returns:
        DateParams object with pre_tell_scripts and in_tell_assignments lists
    """
    result = DateParams()

    # Handle due date
    if due_date is not None:
        pre_script, assignment = create_date_assignment(due_date, "due date", object_var, "dueDate")
        if pre_script:
            result.pre_tell_scripts.append(pre_script)
        if assignment:
            result.in_tell_assignments.append(assignment)

    # Handle defer date
    if defer_date is not None:
        pre_script, assignment = create_date_assignment(
            defer_date, "defer date", object_var, "deferDate"
        )
        if pre_script:
            result.pre_tell_scripts.append(pre_script)
        if assignment:
            result.in_tell_assignments.append(assignment)

    # Handle planned date (OmniFocus 4.7+, tasks only)
    if include_planned and planned_date is not None:
        pre_script, assignment = create_date_assignment(
            planned_date, "planned date", object_var, "plannedDate"
        )
        if pre_script:
            result.pre_tell_scripts.append(pre_script)
        if assignment:
            result.in_tell_assignments.append(assignment)

    return result


def generate_find_clause(
    item_type: str,
    item_var: str,
    item_id: str | None = None,
    item_name: str | None = None,
) -> str:
    """
    Generate AppleScript code to find an item by ID or name.

    Args:
        item_type: Type of item ("task" or "project")
        item_var: Name of the AppleScript variable to store the found item
        item_id: ID of the item (preferred, takes precedence over name)
        item_name: Name of the item (used if ID not provided)

    Returns:
        AppleScript code to find the item

    Raises:
        ValueError: If neither item_id nor item_name is provided
    """
    if not item_id and not item_name:
        raise ValueError("Either item_id or item_name must be provided")

    # Escape inputs
    escaped_id = escape_applescript_string(item_id or "")
    escaped_name = escape_applescript_string(item_name or "")

    entity = "flattened project" if item_type == "project" else "flattened task"

    if escaped_id:
        return f'set {item_var} to first {entity} where id = "{escaped_id}"'
    else:
        return f'set {item_var} to first {entity} where its name = "{escaped_name}"'


def generate_tag_modifications(
    item_var: str,
    add_tags: list[str] | None = None,
    remove_tags: list[str] | None = None,
    replace_tags: list[str] | None = None,
) -> tuple[list[str], list[str]]:
    """
    Generate AppleScript code for tag modifications.

    Handles the logic of choosing between add/remove/replace operations.
    Replace takes precedence over add/remove.

    Args:
        item_var: Name of the AppleScript variable for the item
        add_tags: Tags to add to the item
        remove_tags: Tags to remove from the item
        replace_tags: Tags to replace all existing tags with (takes precedence)

    Returns:
        Tuple of (modifications list, changes list) where:
        - modifications: AppleScript code snippets to execute
        - changes: Human-readable descriptions of what changed
    """
    modifications: list[str] = []
    changes: list[str] = []

    if replace_tags is not None:
        modifications.append(generate_replace_tags_applescript(replace_tags, item_var))
        changes.append("tags (replaced)")
    else:
        if add_tags:
            modifications.append(generate_add_tags_applescript(add_tags, item_var))
            changes.append("tags (added)")
        if remove_tags:
            modifications.append(generate_remove_tags_applescript(remove_tags, item_var))
            changes.append("tags (removed)")

    return modifications, changes
