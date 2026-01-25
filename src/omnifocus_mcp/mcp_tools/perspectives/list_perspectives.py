"""List perspectives tool for OmniFocus."""

from ..response import omnijs_json_response


async def list_perspectives(
    include_built_in: bool = True,
    include_custom: bool = True,
) -> str:
    """
    List all available perspectives in OmniFocus.

    Includes both built-in perspectives (Inbox, Projects, Tags, etc.)
    and custom perspectives (OmniFocus Pro feature).

    Args:
        include_built_in: Include built-in perspectives (default: True)
        include_custom: Include custom perspectives (default: True)

    Returns:
        JSON string with list of perspectives grouped by type
    """
    return await omnijs_json_response(
        "list_perspectives",
        {
            "include_built_in": include_built_in,
            "include_custom": include_custom,
        },
    )
