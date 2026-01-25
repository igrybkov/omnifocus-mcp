"""Add folder tool for OmniFocus."""

import asyncio

from ...utils import escape_applescript_string


async def add_folder(
    name: str,
    parent_folder_name: str | None = None,
) -> str:
    """
    Add a new folder to OmniFocus.

    Args:
        name: The name of the folder
        parent_folder_name: Optional parent folder name to nest this folder in
            (root if not specified)

    Returns:
        Success or error message
    """
    try:
        # Escape user inputs to prevent AppleScript injection
        escaped_name = escape_applescript_string(name)
        escaped_parent = escape_applescript_string(parent_folder_name or "")

        # Determine where to add the folder
        if escaped_parent:
            script = f'''
tell application "OmniFocus"
    tell default document
        set parentFolder to first flattened folder where its name = "{escaped_parent}"
        tell parentFolder
            make new folder with properties {{name:"{escaped_name}"}}
        end tell
    end tell
end tell
return "Folder created successfully in: {escaped_parent}"
'''
        else:
            script = f'''
tell application "OmniFocus"
    tell default document
        make new folder with properties {{name:"{escaped_name}"}}
    end tell
end tell
return "Folder created successfully: {escaped_name}"
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
        return f"Error adding folder: {str(e)}"
