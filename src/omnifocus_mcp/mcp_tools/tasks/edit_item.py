"""Edit item tool for OmniFocus."""

import asyncio

from ...dates import create_date_assignment
from ...tags import (
    generate_add_tags_applescript,
    generate_remove_tags_applescript,
    generate_replace_tags_applescript,
)
from ...utils import escape_applescript_string


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

    Returns:
        Success or error message
    """
    try:
        # Validate inputs
        if not id and not current_name:
            return "Error: Either 'id' or 'current_name' must be provided"

        # Escape all user inputs to prevent AppleScript injection
        escaped_current_name = escape_applescript_string(current_name)
        escaped_id = escape_applescript_string(id or "")
        escaped_new_name = escape_applescript_string(new_name)
        escaped_new_note = escape_applescript_string(new_note)
        escaped_new_folder = escape_applescript_string(new_folder_name or "")

        # Build pre-tell date scripts
        pre_tell_scripts = []
        in_tell_assignments = []

        # Determine item variable name
        item_var = "theProject" if item_type == "project" else "theTask"

        # Handle due date
        if new_due_date is not None:
            pre_script, assignment = create_date_assignment(
                new_due_date, "due date", item_var, "newDueDate"
            )
            if pre_script:
                pre_tell_scripts.append(pre_script)
            if assignment:
                in_tell_assignments.append(assignment)

        # Handle defer date
        if new_defer_date is not None:
            pre_script, assignment = create_date_assignment(
                new_defer_date, "defer date", item_var, "newDeferDate"
            )
            if pre_script:
                pre_tell_scripts.append(pre_script)
            if assignment:
                in_tell_assignments.append(assignment)

        # Handle planned date (tasks only, OmniFocus 4.7+)
        if new_planned_date is not None and item_type == "task":
            pre_script, assignment = create_date_assignment(
                new_planned_date, "planned date", item_var, "newPlannedDate"
            )
            if pre_script:
                pre_tell_scripts.append(pre_script)
            if assignment:
                in_tell_assignments.append(assignment)

        # Build date pre-script
        date_pre_script = "\n\n".join(pre_tell_scripts) if pre_tell_scripts else ""

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
        if item_type == "task":
            # Handle status (new_status takes precedence over mark_complete)
            if new_status is not None:
                if new_status == "completed":
                    modifications.append(f"set completed of {item_var} to true")
                    changes.append("status (completed)")
                elif new_status == "dropped":
                    modifications.append(f"set dropped of {item_var} to true")
                    changes.append("status (dropped)")
                elif new_status == "incomplete":
                    modifications.append(f"set completed of {item_var} to false")
                    modifications.append(f"set dropped of {item_var} to false")
                    changes.append("status (incomplete)")
            elif mark_complete:
                modifications.append(f"set completed of {item_var} to true")
                changes.append("completed")

            # Handle tags
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

        modifications_str = "\n".join(modifications)

        # Build the find clause
        if escaped_id:
            if item_type == "project":
                find_clause = f'set {item_var} to first flattened project where id = "{escaped_id}"'
            else:
                find_clause = f'set {item_var} to first flattened task where id = "{escaped_id}"'
        else:
            if item_type == "project":
                find_clause = f'set {item_var} to first flattened project where its name = "{escaped_current_name}"'
            else:
                find_clause = f'set {item_var} to first flattened task where its name = "{escaped_current_name}"'

        # Build result message
        changes_str = ", ".join(changes) if changes else "no changes"
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

        return stdout.decode().strip()
    except Exception as e:
        return f"Error editing {item_type}: {str(e)}"
