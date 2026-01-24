"""OmniFocus MCP Server - Main server implementation."""

import sys
import asyncio
from typing import Any
from mcp.server.fastmcp import FastMCP

# Create MCP server instance
mcp = FastMCP("OmniFocus MCP Server")


def escape_applescript_string(text: str) -> str:
    """
    Escape a string for safe use in AppleScript.
    
    Args:
        text: The string to escape
        
    Returns:
        Escaped string safe for AppleScript interpolation
    """
    # Escape backslashes first, then quotes
    return text.replace('\\', '\\\\').replace('"', '\\"')


@mcp.tool()
async def dump_database() -> str:
    """
    Export the current state of the OmniFocus database.
    Returns a comprehensive dump of all tasks, projects, and their metadata.
    """
    try:
        # Execute AppleScript to dump OmniFocus database
        script = '''
        tell application "OmniFocus"
            set output to ""
            
            -- Get all projects
            set allProjects to flattened projects of default document
            repeat with aProject in allProjects
                set output to output & "PROJECT: " & name of aProject & return
                set output to output & "  Status: " & (completed of aProject as text) & return
                
                -- Get tasks in this project
                set allTasks to flattened tasks of aProject
                repeat with aTask in allTasks
                    set output to output & "  TASK: " & name of aTask & return
                    set output to output & "    Completed: " & (completed of aTask as text) & return
                    if note of aTask is not missing value then
                        set output to output & "    Note: " & note of aTask & return
                    end if
                end repeat
                set output to output & return
            end repeat
            
            return output
        end tell
        '''
        
        # Run AppleScript via osascript
        proc = await asyncio.create_subprocess_exec(
            'osascript', '-e', script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            return f"Error: {stderr.decode()}"
        
        return stdout.decode()
    except Exception as e:
        return f"Error dumping database: {str(e)}"


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


def main():
    """Main entry point for the MCP server."""
    # Run the server with stdio transport (stdin/stdout)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
