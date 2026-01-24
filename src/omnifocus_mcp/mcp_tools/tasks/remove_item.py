"""Remove item tool for OmniFocus."""

import asyncio
from ...utils import escape_applescript_string


async def remove_item(
    name: str,
    item_type: str = "task",
) -> str:
    """
    Remove a task or project from OmniFocus.
    
    Args:
        name: The name of the task or project to remove
        item_type: Type of item to remove ("task" or "project")
    
    Returns:
        Success or error message
    """
    try:
        # Escape user input to prevent AppleScript injection
        escaped_name = escape_applescript_string(name)
        
        if item_type == "project":
            script = f'''
            tell application "OmniFocus"
                tell default document
                    set theProject to first flattened project where its name = "{escaped_name}"
                    delete theProject
                end tell
            end tell
            return "Project removed successfully: {escaped_name}"
            '''
        else:
            script = f'''
            tell application "OmniFocus"
                tell default document
                    set theTask to first flattened task where its name = "{escaped_name}"
                    delete theTask
                end tell
            end tell
            return "Task removed successfully: {escaped_name}"
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
