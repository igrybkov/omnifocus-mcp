"""Tools for managing OmniFocus projects."""

import asyncio
from .utils import escape_applescript_string


async def add_project(
    name: str,
    note: str = "",
) -> str:
    """
    Add a new project to OmniFocus.
    
    Args:
        name: The name of the project
        note: Optional note/description for the project
    
    Returns:
        Success or error message
    """
    try:
        # Escape user inputs to prevent AppleScript injection
        escaped_name = escape_applescript_string(name)
        escaped_note = escape_applescript_string(note)
        
        script = f'''
        tell application "OmniFocus"
            tell default document
                set newProject to make new project with properties {{name:"{escaped_name}"}}
                if "{escaped_note}" is not "" then
                    set note of newProject to "{escaped_note}"
                end if
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
