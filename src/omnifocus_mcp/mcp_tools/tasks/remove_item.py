"""Remove item tool for OmniFocus."""

import asyncio

from ...applescript_builder import generate_find_clause


async def remove_item(
    name: str = "",
    id: str | None = None,
    item_type: str = "task",
) -> str:
    """
    Remove a task or project from OmniFocus.

    Args:
        name: The name of the task or project to remove (used if id not provided)
        id: The ID of the task or project to remove (preferred)
        item_type: Type of item to remove ("task" or "project")

    Returns:
        Success or error message
    """
    try:
        # Validate inputs
        if not id and not name:
            return "Error: Either 'id' or 'name' must be provided"

        # Build the find clause
        find_clause = generate_find_clause(item_type, "theItem", id, name)

        # Build result message
        if id:
            result_msg = f"{item_type.capitalize()} removed successfully (by ID)"
        else:
            result_msg = f"{item_type.capitalize()} removed successfully: {name}"

        script = f'''
tell application "OmniFocus"
    tell default document
        {find_clause}
        delete theItem
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
        return f"Error removing {item_type}: {str(e)}"
