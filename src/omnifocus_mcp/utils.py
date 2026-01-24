"""Utility functions for OmniFocus MCP server."""


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
