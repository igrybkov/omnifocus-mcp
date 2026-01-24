"""Edit item tool for OmniFocus."""

import asyncio
from ...utils import escape_applescript_string


async def edit_item(
    current_name: str,
    new_name: str = "",
    new_note: str = "",
    mark_complete: bool = False,
    item_type: str = "task",
) -> str:
    """
    Edit a task or project in OmniFocus.
    
    Args:
        current_name: The current name of the task or project
        new_name: New name for the item (optional)
        new_note: New note for the item (optional)
        mark_complete: Whether to mark the item as complete
        item_type: Type of item to edit ("task" or "project")
    
    Returns:
        Success or error message
    """
    try:
        # Escape all user inputs to prevent AppleScript injection
        escaped_current_name = escape_applescript_string(current_name)
        escaped_new_name = escape_applescript_string(new_name)
        escaped_new_note = escape_applescript_string(new_note)
        
        if item_type == "project":
            script = f'''
            tell application "OmniFocus"
                tell default document
                    set theProject to first flattened project where its name = "{escaped_current_name}"
                    if "{escaped_new_name}" is not "" then
                        set name of theProject to "{escaped_new_name}"
                    end if
                    if "{escaped_new_note}" is not "" then
                        set note of theProject to "{escaped_new_note}"
                    end if
                    if {str(mark_complete).lower()} then
                        set completed of theProject to true
                    end if
                end tell
            end tell
            return "Project updated successfully"
            '''
        else:
            script = f'''
            tell application "OmniFocus"
                tell default document
                    set theTask to first flattened task where its name = "{escaped_current_name}"
                    if "{escaped_new_name}" is not "" then
                        set name of theTask to "{escaped_new_name}"
                    end if
                    if "{escaped_new_note}" is not "" then
                        set note of theTask to "{escaped_new_note}"
                    end if
                    if {str(mark_complete).lower()} then
                        set completed of theTask to true
                    end if
                end tell
            end tell
            return "Task updated successfully"
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
        return f"Error editing {item_type}: {str(e)}"
