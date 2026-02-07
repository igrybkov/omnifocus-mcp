"""Edit item tool for OmniFocus."""

import asyncio

from ...applescript_builder import (
    generate_find_clause,
    generate_tag_modifications,
    process_date_params,
)
from ...utils import escape_applescript_string
from ..reorder.move_helper import move_task_to_parent, move_task_to_position
from .status_helper import change_task_status


async def edit_item(
    current_name: str = "",
    id: str | None = None,
    new_name: str = "",
    new_note: str = "",
    mark_complete: bool = False,
    item_type: str = "task",
    new_due_date: str | None = None,
    new_defer_date: str | None = None,
    new_planned_date: str | None = None,
    new_flagged: bool | None = None,
    new_estimated_minutes: int | None = None,
    new_status: str | None = None,
    add_tags: list[str] | None = None,
    remove_tags: list[str] | None = None,
    replace_tags: list[str] | None = None,
    new_sequential: bool | None = None,
    new_folder_name: str | None = None,
    new_project_status: str | None = None,
    new_parent_id: str | None = None,
    new_position: str | None = None,
    position_reference_task_id: str | None = None,
) -> str:
    """
    Edit a task or project in OmniFocus.

    Args:
        current_name: The current name of the task or project (used if id not provided)
        id: The ID of the task or project to edit (preferred)
        new_name: New name for the item (optional)
        new_note: New note for the item (optional)
        mark_complete: Whether to mark the item as complete (deprecated, use new_status)
        item_type: Type of item to edit ("task" or "project")
        new_due_date: New due date in ISO format, empty string to clear (optional)
        new_defer_date: New defer date in ISO format, empty string to clear (optional)
        new_planned_date: New planned date in ISO format, empty string to clear (tasks only,
            OmniFocus 4.7+)
        new_flagged: New flagged status (optional)
        new_estimated_minutes: New estimated minutes (optional)
        new_status: New status for tasks: 'incomplete', 'completed', 'dropped' (optional)
        add_tags: Tags to add to the item (optional)
        remove_tags: Tags to remove from the item (optional)
        replace_tags: Tags to replace all existing tags with (optional)
        new_sequential: Whether the project should be sequential (projects only, optional)
        new_folder_name: New folder to move the project to (projects only, optional)
        new_project_status: New status for projects: 'active', 'completed', 'dropped', 'onHold' (optional)
        new_parent_id: New parent task or project ID (tasks only, optional).
            Use empty string to un-nest (move to project root).
        new_position: New position within container - 'beginning', 'ending', 'before', 'after'
            (tasks only, not supported for inbox tasks or projects)
        position_reference_task_id: ID of reference task (required when new_position is
            'before' or 'after')

    Returns:
        Success or error message
    """
    try:
        # Validate inputs
        if not id and not current_name:
            return "Error: Either 'id' or 'current_name' must be provided"

        # Escape user inputs to prevent AppleScript injection
        escaped_new_name = escape_applescript_string(new_name)
        escaped_new_note = escape_applescript_string(new_note)
        escaped_new_folder = escape_applescript_string(new_folder_name or "")

        # Determine item variable name
        item_var = "theProject" if item_type == "project" else "theTask"

        # Process date parameters (planned_date only for tasks)
        date_params = process_date_params(
            item_var,
            due_date=new_due_date,
            defer_date=new_defer_date,
            planned_date=new_planned_date,
            include_planned=(item_type == "task"),
        )
        date_pre_script = date_params.pre_tell_script
        in_tell_assignments = date_params.in_tell_assignments

        # Build changes list for tracking what was modified
        changes = []

        # Build modifications
        modifications = []

        if escaped_new_name:
            modifications.append(f'set name of {item_var} to "{escaped_new_name}"')
            changes.append("name")

        if escaped_new_note:
            modifications.append(f'set note of {item_var} to "{escaped_new_note}"')
            changes.append("note")

        if new_flagged is not None:
            modifications.append(f"set flagged of {item_var} to {str(new_flagged).lower()}")
            changes.append("flagged")

        if new_estimated_minutes is not None:
            modifications.append(f"set estimated minutes of {item_var} to {new_estimated_minutes}")
            changes.append("estimated minutes")

        # Add date assignments
        modifications.extend(in_tell_assignments)
        if new_due_date is not None:
            changes.append("due date")
        if new_defer_date is not None:
            changes.append("defer date")
        if new_planned_date is not None and item_type == "task":
            changes.append("planned date")

        # Handle task-specific properties
        effective_status = None  # Will be set if task status change is needed
        if item_type == "task":
            # Determine effective status change (new_status takes precedence over mark_complete)
            # Status is handled via OmniJS post-edit (works for all task types including inbox)
            if new_status is not None:
                effective_status = new_status
                changes.append(f"status ({new_status})")
            elif mark_complete:
                effective_status = "completed"
                changes.append("completed")

            # Handle tags
            tag_mods, tag_changes = generate_tag_modifications(
                item_var, add_tags, remove_tags, replace_tags
            )
            modifications.extend(tag_mods)
            changes.extend(tag_changes)

        # Handle project-specific properties
        if item_type == "project":
            if new_sequential is not None:
                modifications.append(
                    f"set sequential of {item_var} to {str(new_sequential).lower()}"
                )
                changes.append("sequential")

            if new_project_status is not None:
                if new_project_status == "active":
                    modifications.append(f"set status of {item_var} to active status")
                    changes.append("status (active)")
                elif new_project_status == "completed":
                    modifications.append(f"set completed of {item_var} to true")
                    changes.append("status (completed)")
                elif new_project_status == "dropped":
                    modifications.append(f"set status of {item_var} to dropped status")
                    changes.append("status (dropped)")
                elif new_project_status == "onHold":
                    modifications.append(f"set status of {item_var} to on hold status")
                    changes.append("status (on hold)")
            elif mark_complete:
                modifications.append(f"set completed of {item_var} to true")
                changes.append("completed")

            # Handle folder move
            if escaped_new_folder:
                modifications.append(f'''
set targetFolder to first flattened folder where its name = "{escaped_new_folder}"
move {item_var} to end of projects of targetFolder''')
                changes.append("folder")

            # Handle tags for projects too
            tag_mods, tag_changes = generate_tag_modifications(
                item_var, add_tags, remove_tags, replace_tags
            )
            modifications.extend(tag_mods)
            changes.extend(tag_changes)

        modifications_str = "\n".join(modifications)

        # Build the find clause
        find_clause = generate_find_clause(item_type, item_var, id, current_name)

        # Build result message
        changes_str = ", ".join(changes) if changes else "no changes"

        # Check if we need post-edit operations (status, parent, or position change)
        needs_task_id = item_type == "task" and (
            effective_status is not None or new_parent_id is not None or new_position
        )

        # For tasks with parent/position change, we need the task ID
        if needs_task_id:
            script = f"""
{date_pre_script}
tell application "OmniFocus"
    tell default document
        {find_clause}
        {modifications_str}
        return id of {item_var}
    end tell
end tell
"""
        else:
            result_msg = f"{item_type.capitalize()} updated successfully. Changed: {changes_str}"
            script = f'''
{date_pre_script}
tell application "OmniFocus"
    tell default document
        {find_clause}
        {modifications_str}
    end tell
end tell
return "{result_msg}"
'''

        proc = await asyncio.create_subprocess_exec(
            "osascript",
            "-e",
            script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"Error: {stderr.decode()}"

        output = stdout.decode().strip()

        # Handle post-edit operations for tasks
        if needs_task_id:
            task_id = output  # The script returned the task ID
            result_msg = f"Task updated successfully. Changed: {changes_str}"

            # Handle status change via OmniJS (works for all task types including inbox)
            if effective_status is not None:
                success, status_msg = await change_task_status(task_id, effective_status)
                if not success:
                    result_msg += f" (status change failed: {status_msg})"

            # Handle parent change (if specified)
            if new_parent_id is not None:
                success, parent_msg = await move_task_to_parent(task_id, new_parent_id)
                if success:
                    if new_parent_id == "":
                        result_msg += " (moved to project root)"
                    else:
                        result_msg += " (moved to new parent)"
                    changes.append("parent")
                else:
                    result_msg += f" (parent change failed: {parent_msg})"

            # Handle position change (if specified)
            if new_position:
                success, move_msg = await move_task_to_position(
                    task_id, new_position, position_reference_task_id
                )
                if success:
                    result_msg += f" (repositioned to {new_position})"
                    changes.append("position")
                else:
                    result_msg += f" (repositioning failed: {move_msg})"

            return result_msg

        return output
    except Exception as e:
        return f"Error editing {item_type}: {str(e)}"
