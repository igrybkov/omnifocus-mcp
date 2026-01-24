"""Add task tool for OmniFocus."""

import asyncio
from ...utils import escape_applescript_string


async def add_omnifocus_task(
    name: str,
    note: str = "",
    project: str = "",
) -> str:
    """
    Add a new task to OmniFocus.
    
    Args:
        name: The name/title of the task
        note: Optional note/description for the task
        project: Optional project name to add the task to
    
    Returns:
        Success or error message
    """
    try:
        # Escape all user inputs to prevent AppleScript injection
        escaped_name = escape_applescript_string(name)
        escaped_note = escape_applescript_string(note)
        escaped_project = escape_applescript_string(project)
        
        # Build AppleScript to add task
        if project:
            script = f'''
            tell application "OmniFocus"
                tell default document
                    set theProject to first flattened project where its name = "{escaped_project}"
                    tell theProject
                        set newTask to make new task with properties {{name:"{escaped_name}"}}
                        if "{escaped_note}" is not "" then
                            set note of newTask to "{escaped_note}"
                        end if
                    end tell
                end tell
            end tell
            return "Task added successfully to project: {escaped_project}"
            '''
        else:
            script = f'''
            tell application "OmniFocus"
                tell default document
                    set newTask to make new inbox task with properties {{name:"{escaped_name}"}}
                    if "{escaped_note}" is not "" then
                        set note of newTask to "{escaped_note}"
                    end if
                end tell
            end tell
            return "Task added successfully to inbox"
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
        return f"Error adding task: {str(e)}"
