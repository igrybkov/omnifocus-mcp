"""Add project tool for OmniFocus."""

import asyncio
from typing import Optional
from ...utils import escape_applescript_string
from ...dates import create_date_assignment
from ...tags import generate_add_tags_applescript


async def add_project(
    name: str,
    note: str = "",
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    flagged: Optional[bool] = None,
    estimated_minutes: Optional[int] = None,
    tags: Optional[list[str]] = None,
    folder_name: Optional[str] = None,
    sequential: Optional[bool] = None,
) -> str:
    """
    Add a new project to OmniFocus.

    Args:
        name: The name of the project
        note: Optional note/description for the project
        due_date: Optional due date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        defer_date: Optional defer date in ISO format
        flagged: Optional flag status
        estimated_minutes: Optional estimated time to complete, in minutes
        tags: Optional list of tags to assign to the project
        folder_name: Optional folder name to add project to (root if not specified)
        sequential: Optional whether tasks in the project should be sequential (default: parallel)

    Returns:
        Success or error message
    """
    try:
        # Escape user inputs to prevent AppleScript injection
        escaped_name = escape_applescript_string(name)
        escaped_note = escape_applescript_string(note)
        escaped_folder = escape_applescript_string(folder_name or "")

        # Build pre-tell date scripts
        pre_tell_scripts = []
        in_tell_assignments = []

        # Handle due date
        if due_date is not None:
            pre_script, assignment = create_date_assignment(
                due_date, "due date", "newProject", "dueDate"
            )
            if pre_script:
                pre_tell_scripts.append(pre_script)
            if assignment:
                in_tell_assignments.append(assignment)

        # Handle defer date
        if defer_date is not None:
            pre_script, assignment = create_date_assignment(
                defer_date, "defer date", "newProject", "deferDate"
            )
            if pre_script:
                pre_tell_scripts.append(pre_script)
            if assignment:
                in_tell_assignments.append(assignment)

        # Build date pre-script
        date_pre_script = "\n\n".join(pre_tell_scripts) if pre_tell_scripts else ""

        # Build project properties
        properties = [f'name:"{escaped_name}"']
        if flagged is not None:
            properties.append(f"flagged:{str(flagged).lower()}")
        if estimated_minutes is not None:
            properties.append(f"estimated minutes:{estimated_minutes}")
        if sequential is not None:
            properties.append(f"sequential:{str(sequential).lower()}")

        properties_str = ", ".join(properties)

        # Build post-creation assignments
        post_creation = []
        if escaped_note:
            post_creation.append(f'set note of newProject to "{escaped_note}"')
        post_creation.extend(in_tell_assignments)

        # Add tags if specified
        if tags:
            post_creation.append(generate_add_tags_applescript(tags, "newProject"))

        post_creation_str = "\n".join(post_creation)

        # Determine where to add the project
        if escaped_folder:
            script = f'''
{date_pre_script}
tell application "OmniFocus"
    tell default document
        set theFolder to first flattened folder where its name = "{escaped_folder}"
        tell theFolder
            set newProject to make new project with properties {{{properties_str}}}
            {post_creation_str}
        end tell
    end tell
end tell
return "Project created successfully in folder: {escaped_folder}"
'''
        else:
            script = f'''
{date_pre_script}
tell application "OmniFocus"
    tell default document
        set newProject to make new project with properties {{{properties_str}}}
        {post_creation_str}
    end tell
end tell
return "Project created successfully: {escaped_name}"
'''

        proc = await asyncio.create_subprocess_exec(
            'osascript', '-e', script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"Error: {stderr.decode()}"

        return stdout.decode().strip()
    except Exception as e:
        return f"Error adding project: {str(e)}"
