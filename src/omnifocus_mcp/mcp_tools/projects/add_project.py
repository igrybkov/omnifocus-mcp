"""Add project tool for OmniFocus."""

import asyncio

from ...applescript_builder import process_date_params
from ...markdown_notes import apply_note
from ...tags import generate_add_tags_applescript
from ...utils import escape_applescript_string


async def add_project(
    name: str,
    note: str = "",
    due_date: str | None = None,
    defer_date: str | None = None,
    flagged: bool | None = None,
    estimated_minutes: int | None = None,
    tags: list[str] | None = None,
    folder_name: str | None = None,
    sequential: bool | None = None,
) -> str:
    """
    Add a new project to OmniFocus.

    Args:
        name: The name of the project
        note: Optional note in Markdown. Bold, italic, inline code, links, headings,
            and lists are converted to OmniFocus-native rich text. Notes are also
            returned as Markdown when read.
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
        # Escape user inputs to prevent AppleScript injection.
        # The note is applied separately as rich text (Markdown) via OmniJS below.
        escaped_name = escape_applescript_string(name)
        escaped_folder = escape_applescript_string(folder_name or "")

        # Process date parameters (projects don't have planned_date)
        date_params = process_date_params(
            "newProject",
            due_date=due_date,
            defer_date=defer_date,
            include_planned=False,
        )
        date_pre_script = date_params.pre_tell_script
        in_tell_assignments = date_params.in_tell_assignments

        # Build project properties
        properties = [f'name:"{escaped_name}"']
        if flagged is not None:
            properties.append(f"flagged:{str(flagged).lower()}")
        if estimated_minutes is not None:
            properties.append(f"estimated minutes:{estimated_minutes}")
        if sequential is not None:
            properties.append(f"sequential:{str(sequential).lower()}")

        properties_str = ", ".join(properties)

        # Build post-creation assignments (note is set later via OmniJS as rich text)
        post_creation = []
        post_creation.extend(in_tell_assignments)

        # Add tags if specified
        if tags:
            post_creation.append(generate_add_tags_applescript(tags, "newProject"))

        post_creation_str = "\n".join(post_creation)

        # Determine where to add the project. Scripts return the project ID so the
        # note can be applied afterward as rich text via OmniJS.
        if escaped_folder:
            location_msg = f"in folder: {escaped_folder}"
            script = f'''
{date_pre_script}
tell application "OmniFocus"
    tell default document
        set theFolder to first flattened folder where its name = "{escaped_folder}"
        tell theFolder
            set newProject to make new project with properties {{{properties_str}}}
            {post_creation_str}
        end tell
        return id of newProject
    end tell
end tell
'''
        else:
            location_msg = f"{escaped_name}"
            script = f"""
{date_pre_script}
tell application "OmniFocus"
    tell default document
        set newProject to make new project with properties {{{properties_str}}}
        {post_creation_str}
        return id of newProject
    end tell
end tell
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

        project_id = stdout.decode().strip()
        result_msg = f"Project created successfully {location_msg}"

        # Apply the note as rich text (Markdown -> OmniFocus native) via OmniJS
        if note:
            note_ok, note_msg = await apply_note(project_id, note)
            if not note_ok:
                result_msg += f" (note not set: {note_msg})"

        return result_msg
    except Exception as e:
        return f"Error adding project: {str(e)}"
