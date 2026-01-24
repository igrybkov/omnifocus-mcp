"""Remove item tool for OmniFocus."""

import asyncio
from typing import Optional
from ...utils import escape_applescript_string


async def remove_item(
    name: str = "",
    id: Optional[str] = None,
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

        # Escape user input to prevent AppleScript injection
        escaped_name = escape_applescript_string(name)
        escaped_id = escape_applescript_string(id or "")

        # Build the find clause
        if escaped_id:
            if item_type == "project":
                find_clause = f'set theItem to first flattened project where id = "{escaped_id}"'
                result_msg = f"Project removed successfully (by ID)"
            else:
                find_clause = f'set theItem to first flattened task where id = "{escaped_id}"'
                result_msg = f"Task removed successfully (by ID)"
        else:
            if item_type == "project":
                find_clause = f'set theItem to first flattened project where its name = "{escaped_name}"'
                result_msg = f"Project removed successfully: {escaped_name}"
            else:
                find_clause = f'set theItem to first flattened task where its name = "{escaped_name}"'
                result_msg = f"Task removed successfully: {escaped_name}"

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
            'osascript', '-e', script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return f"Error: {stderr.decode()}"

        return stdout.decode().strip()
    except Exception as e:
        return f"Error removing {item_type}: {str(e)}"
