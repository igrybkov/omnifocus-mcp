"""Debug and diagnostic tools for OmniFocus."""

import asyncio


async def dump_database() -> str:
    """
    Export the current state of the OmniFocus database.
    Returns a comprehensive dump of all tasks, projects, and their metadata.
    
    NOTE: This tool is only available when running with --expanded flag.
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
