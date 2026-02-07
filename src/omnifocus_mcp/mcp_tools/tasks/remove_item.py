"""Remove item tool for OmniFocus.

Note: This tool drops items (marks them as dropped) instead of physically deleting them.
This preserves data and allows recovery if needed.
"""

import asyncio

from ...applescript_builder import generate_find_clause
from .status_helper import change_task_status


async def remove_item(
    name: str = "",
    id: str | None = None,
    item_type: str = "task",
) -> str:
    """
    Remove a task or project from OmniFocus.

    Note: Items are dropped (marked as dropped status) rather than physically deleted.
    This preserves data and allows recovery if needed.

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

        # Build result message
        if id:
            result_msg = f"{item_type.capitalize()} dropped successfully (by ID)"
        else:
            result_msg = f"{item_type.capitalize()} dropped successfully: {name}"

        # Projects: use AppleScript (no inbox issue for projects)
        if item_type == "project":
            find_clause = generate_find_clause(item_type, "theItem", id, name)
            script = f'''
tell application "OmniFocus"
    tell default document
        {find_clause}
        set status of theItem to dropped status
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

        # Tasks: use OmniJS (handles inbox tasks correctly)
        task_id = id
        if not task_id:
            # Resolve name to ID via AppleScript
            find_clause = generate_find_clause(item_type, "theItem", id, name)
            script = f"""
tell application "OmniFocus"
    tell default document
        {find_clause}
        return id of theItem
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

            task_id = stdout.decode().strip()

        success, msg = await change_task_status(task_id, "dropped")
        if success:
            return result_msg
        else:
            return f"Error: {msg}"

    except Exception as e:
        return f"Error removing {item_type}: {str(e)}"
