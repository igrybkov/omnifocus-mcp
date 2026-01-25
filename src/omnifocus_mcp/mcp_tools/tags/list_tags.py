"""List tags tool for OmniFocus."""

from ..response import omnijs_json_response


async def list_tags(
    include_nested: bool = True,
    include_counts: bool = True,
) -> str:
    """
    List all tags in OmniFocus.

    Returns a hierarchical tree of tags with optional task counts.

    Args:
        include_nested: Include nested/child tags (default: True).
            If False, returns only top-level tags.
        include_counts: Include count of active tasks for each tag (default: True)

    Returns:
        JSON string with list of tags in the following format:
        {
            "total": <number of tags>,
            "tags": [
                {
                    "id": <tag id>,
                    "name": <tag name>,
                    "parent": <parent tag name or null>,
                    "allowsNextAction": <boolean>,
                    "activeTaskCount": <number if include_counts=true>,
                    "children": [<nested tags if include_nested=true>]
                },
                ...
            ]
        }
    """
    return await omnijs_json_response(
        "list_tags",
        {
            "include_nested": include_nested,
            "include_counts": include_counts,
        },
    )
