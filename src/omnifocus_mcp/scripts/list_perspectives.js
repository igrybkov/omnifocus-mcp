// List all available perspectives in OmniFocus
// Params: { include_built_in: boolean, include_custom: boolean }

try {
    const perspectives = [];

    // Built-in perspectives
    if (params.include_built_in) {
        const builtInPerspectives = [
            { name: 'Inbox', description: 'Tasks not yet assigned to a project' },
            { name: 'Projects', description: 'All projects organized by folder' },
            { name: 'Tags', description: 'Tasks organized by tags' },
            { name: 'Forecast', description: 'Calendar view of due and deferred items' },
            { name: 'Flagged', description: 'Flagged items' },
            { name: 'Review', description: 'Projects due for review' }
        ];

        builtInPerspectives.forEach(p => {
            perspectives.push({
                id: 'builtin_' + p.name.toLowerCase(),
                name: p.name,
                type: 'builtin',
                description: p.description,
                isBuiltIn: true,
                canModify: false
            });
        });
    }

    // Custom perspectives (Pro feature)
    if (params.include_custom) {
        try {
            const customPerspectives = Perspective.Custom.all;
            if (customPerspectives && customPerspectives.length > 0) {
                customPerspectives.forEach(p => {
                    perspectives.push({
                        id: p.id ? p.id.primaryKey : 'custom_' + p.name.toLowerCase().replace(/\s+/g, '_'),
                        name: p.name,
                        type: 'custom',
                        isBuiltIn: false,
                        canModify: true
                    });
                });
            }
        } catch (e) {
            // Custom perspectives might not be available (Standard edition)
        }
    }

    // Count by type
    const builtInCount = perspectives.filter(p => p.type === 'builtin').length;
    const customCount = perspectives.filter(p => p.type === 'custom').length;

    return JSON.stringify({
        total: perspectives.length,
        builtInCount: builtInCount,
        customCount: customCount,
        perspectives: perspectives
    });

} catch (error) {
    return JSON.stringify({
        error: "Error listing perspectives: " + error.toString()
    });
}
