"""Tag utilities for OmniFocus AppleScript generation."""

from .utils import escape_applescript_string


def generate_add_tags_applescript(tags: list[str], item_var: str) -> str:
    """
    Generate AppleScript code to add tags to an item.

    Tags are created if they don't exist, then added to the item.

    Args:
        tags: List of tag names to add
        item_var: Name of the AppleScript variable for the item

    Returns:
        AppleScript code to add the tags
    """
    if not tags:
        return ""

    lines = []
    for tag in tags:
        escaped_tag = escape_applescript_string(tag)
        lines.append(f'''
try
    set theTag to first flattened tag where name = "{escaped_tag}"
on error
    set theTag to make new tag with properties {{name:"{escaped_tag}"}}
end try
add theTag to tags of {item_var}''')

    return "\n".join(lines)


def generate_remove_tags_applescript(tags: list[str], item_var: str) -> str:
    """
    Generate AppleScript code to remove tags from an item.

    Args:
        tags: List of tag names to remove
        item_var: Name of the AppleScript variable for the item

    Returns:
        AppleScript code to remove the tags
    """
    if not tags:
        return ""

    lines = []
    for tag in tags:
        escaped_tag = escape_applescript_string(tag)
        lines.append(f'''
try
    set theTag to first flattened tag where name = "{escaped_tag}"
    remove theTag from tags of {item_var}
end try''')

    return "\n".join(lines)


def generate_replace_tags_applescript(tags: list[str], item_var: str) -> str:
    """
    Generate AppleScript code to replace all tags on an item.

    First removes all existing tags, then adds the new ones.

    Args:
        tags: List of tag names to set (replaces all existing tags)
        item_var: Name of the AppleScript variable for the item

    Returns:
        AppleScript code to replace the tags
    """
    # First, clear all existing tags
    clear_script = f"""
set existingTags to tags of {item_var}
repeat with existingTag in existingTags
    remove existingTag from tags of {item_var}
end repeat"""

    # Then add the new tags
    add_script = generate_add_tags_applescript(tags, item_var)

    return clear_script + "\n" + add_script
