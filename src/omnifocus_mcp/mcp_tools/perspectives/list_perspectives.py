"""List perspectives tool for OmniFocus."""

import json
from ...omnijs import execute_omnijs


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
    script = f'''
    (() => {{
        try {{
            const perspectives = [];

            // Built-in perspectives
            if ({str(include_built_in).lower()}) {{
                const builtInPerspectives = [
                    {{ name: 'Inbox', description: 'Tasks not yet assigned to a project' }},
                    {{ name: 'Projects', description: 'All projects organized by folder' }},
                    {{ name: 'Tags', description: 'Tasks organized by tags' }},
                    {{ name: 'Forecast', description: 'Calendar view of due and deferred items' }},
                    {{ name: 'Flagged', description: 'Flagged items' }},
                    {{ name: 'Review', description: 'Projects due for review' }}
                ];

                builtInPerspectives.forEach(p => {{
                    perspectives.push({{
                        id: 'builtin_' + p.name.toLowerCase(),
                        name: p.name,
                        type: 'builtin',
                        description: p.description,
                        isBuiltIn: true,
                        canModify: false
                    }});
                }});
            }}

            // Custom perspectives (Pro feature)
            if ({str(include_custom).lower()}) {{
                try {{
                    const customPerspectives = Perspective.Custom.all;
                    if (customPerspectives && customPerspectives.length > 0) {{
                        customPerspectives.forEach(p => {{
                            perspectives.push({{
                                id: p.id ? p.id.primaryKey : 'custom_' + p.name.toLowerCase().replace(/\\s+/g, '_'),
                                name: p.name,
                                type: 'custom',
                                isBuiltIn: false,
                                canModify: true
                            }});
                        }});
                    }}
                }} catch (e) {{
                    // Custom perspectives might not be available (Standard edition)
                }}
            }}

            // Count by type
            const builtInCount = perspectives.filter(p => p.type === 'builtin').length;
            const customCount = perspectives.filter(p => p.type === 'custom').length;

            return JSON.stringify({{
                total: perspectives.length,
                builtInCount: builtInCount,
                customCount: customCount,
                perspectives: perspectives
            }});

        }} catch (error) {{
            return JSON.stringify({{
                error: "Error listing perspectives: " + error.toString()
            }});
        }}
    }})();
    '''

    try:
        result = await execute_omnijs(script)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
