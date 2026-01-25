"""List perspectives tool for OmniFocus."""

import json

from ...omnijs import execute_omnijs_with_params


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
    try:
        result = await execute_omnijs_with_params(
            "list_perspectives",
            {
                "include_built_in": include_built_in,
                "include_custom": include_custom,
            },
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
