"""Add task tool for OmniFocus."""

import asyncio

from ...dates import create_date_assignment
from ...tags import generate_add_tags_applescript
from ...utils import escape_applescript_string


async def add_omnifocus_task(
    name: str,
    note: str = "",
    project: str = "",
    due_date: str | None = None,
    defer_date: str | None = None,
    planned_date: str | None = None,
    flagged: bool | None = None,
    estimated_minutes: int | None = None,
    tags: list[str] | None = None,
    parent_task_id: str | None = None,
    parent_task_name: str | None = None,
) -> str:
    """
    Add a new task to OmniFocus.

    Args:
        name: The name/title of the task
        note: Optional note/description for the task
        project: Optional project name to add the task to (adds to inbox if not specified)
        due_date: Optional due date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        defer_date: Optional defer date in ISO format
        planned_date: Optional planned date in ISO format - indicates intention to work on
            this task on this date (OmniFocus 4.7+)
        flagged: Optional flag status
        estimated_minutes: Optional estimated time to complete, in minutes
        tags: Optional list of tags to assign to the task
        parent_task_id: Optional ID of the parent task (for creating subtasks)
        parent_task_name: Optional name of parent task (used if ID not provided)

    Returns:
        Success or error message
    """
    try:
        # Escape all user inputs to prevent AppleScript injection
        escaped_name = escape_applescript_string(name)
        escaped_note = escape_applescript_string(note)
        escaped_project = escape_applescript_string(project)
        escaped_parent_id = escape_applescript_string(parent_task_id or "")
        escaped_parent_name = escape_applescript_string(parent_task_name or "")

        # Build pre-tell date scripts
        pre_tell_scripts = []
        in_tell_assignments = []

        # Handle due date
        if due_date is not None:
            pre_script, assignment = create_date_assignment(
                due_date, "due date", "newTask", "dueDate"
            )
            if pre_script:
                pre_tell_scripts.append(pre_script)
            if assignment:
                in_tell_assignments.append(assignment)

        # Handle defer date
        if defer_date is not None:
            pre_script, assignment = create_date_assignment(
                defer_date, "defer date", "newTask", "deferDate"
            )
            if pre_script:
                pre_tell_scripts.append(pre_script)
            if assignment:
                in_tell_assignments.append(assignment)

        # Handle planned date (OmniFocus 4.7+)
        if planned_date is not None:
            pre_script, assignment = create_date_assignment(
                planned_date, "planned date", "newTask", "plannedDate"
            )
            if pre_script:
                pre_tell_scripts.append(pre_script)
            if assignment:
                in_tell_assignments.append(assignment)

        # Build date pre-script
        date_pre_script = "\n\n".join(pre_tell_scripts) if pre_tell_scripts else ""

        # Build task properties
        properties = [f'name:"{escaped_name}"']
        if flagged is not None:
            properties.append(f"flagged:{str(flagged).lower()}")
        if estimated_minutes is not None:
            # OmniFocus uses seconds internally
            properties.append(f"estimated minutes:{estimated_minutes}")

        properties_str = ", ".join(properties)

        # Build post-creation assignments
        post_creation = []
        if escaped_note:
            post_creation.append(f'set note of newTask to "{escaped_note}"')
        post_creation.extend(in_tell_assignments)

        # Add tags if specified
        if tags:
            post_creation.append(generate_add_tags_applescript(tags, "newTask"))

        post_creation_str = "\n".join(post_creation)

        # Determine where to add the task
        if escaped_parent_id:
            # Add as subtask by parent ID
            script = f'''
{date_pre_script}
tell application "OmniFocus"
    tell default document
        set parentTask to first flattened task where id = "{escaped_parent_id}"
        tell parentTask
            set newTask to make new task with properties {{{properties_str}}}
            {post_creation_str}
        end tell
    end tell
end tell
return "Task added successfully as subtask (by ID)"
'''
        elif escaped_parent_name:
            # Add as subtask by parent name
            if escaped_project:
                # Search within project first
                script = f'''
{date_pre_script}
tell application "OmniFocus"
    tell default document
        set theProject to first flattened project where its name = "{escaped_project}"
        set parentTask to first flattened task of theProject where name = "{escaped_parent_name}"
        tell parentTask
            set newTask to make new task with properties {{{properties_str}}}
            {post_creation_str}
        end tell
    end tell
end tell
return "Task added successfully as subtask in project: {escaped_project}"
'''
            else:
                # Search globally
                script = f'''
{date_pre_script}
tell application "OmniFocus"
    tell default document
        set parentTask to first flattened task where name = "{escaped_parent_name}"
        tell parentTask
            set newTask to make new task with properties {{{properties_str}}}
            {post_creation_str}
        end tell
    end tell
end tell
return "Task added successfully as subtask"
'''
        elif escaped_project:
            # Add to project
            script = f'''
{date_pre_script}
tell application "OmniFocus"
    tell default document
        set theProject to first flattened project where its name = "{escaped_project}"
        tell theProject
            set newTask to make new task with properties {{{properties_str}}}
            {post_creation_str}
        end tell
    end tell
end tell
return "Task added successfully to project: {escaped_project}"
'''
        else:
            # Add to inbox
            script = f"""
{date_pre_script}
tell application "OmniFocus"
    tell default document
        set newTask to make new inbox task with properties {{{properties_str}}}
        {post_creation_str}
    end tell
end tell
return "Task added successfully to inbox"
"""

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
        return f"Error adding task: {str(e)}"
