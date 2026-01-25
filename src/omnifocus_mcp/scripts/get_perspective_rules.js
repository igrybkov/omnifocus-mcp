// Get filter rules for a custom OmniFocus perspective
// Params: { perspective_name: string, resolve_ids: boolean }

try {
    const perspectiveName = params.perspective_name;
    const resolveIds = params.resolve_ids !== false; // default true
    const normalizedName = perspectiveName.toLowerCase();

    // Find the perspective
    const customPersp = Perspective.Custom.all.find(
        p => p.name.toLowerCase() === normalizedName
    );

    if (!customPersp) {
        // List available perspectives to help user
        const available = Perspective.Custom.all.map(p => p.name);
        return JSON.stringify({
            error: "Perspective not found: " + perspectiveName,
            availablePerspectives: available
        });
    }

    // Build tag ID to name lookup
    const tagIdToName = {};
    if (resolveIds) {
        flattenedTags.forEach(tag => {
            tagIdToName[tag.id.primaryKey] = tag.name;
        });
    }

    // Build folder ID to name/path lookup
    const folderIdToPath = {};
    if (resolveIds) {
        flattenedFolders.forEach(folder => {
            const pathParts = [];
            let current = folder;
            while (current) {
                pathParts.unshift(current.name);
                current = current.parent;
            }
            folderIdToPath[folder.id.primaryKey] = pathParts.join(" > ");
        });
        // Also include projects for actionWithinFocus
        flattenedProjects.forEach(project => {
            folderIdToPath[project.id.primaryKey] = project.name;
        });
    }

    // Recursively resolve IDs in rules
    function resolveRule(rule) {
        if (!rule || typeof rule !== 'object') {
            return rule;
        }

        if (Array.isArray(rule)) {
            return rule.map(r => resolveRule(r));
        }

        const resolved = {};
        for (const key in rule) {
            const value = rule[key];

            if (key === 'actionHasAnyOfTags' && Array.isArray(value) && resolveIds) {
                // Resolve tag IDs to names
                resolved[key] = value.map(id => tagIdToName[id] || id);
                resolved['_originalTagIds'] = value;
            } else if (key === 'actionWithinFocus' && Array.isArray(value) && resolveIds) {
                // Resolve folder/project IDs to names
                resolved[key] = value.map(id => folderIdToPath[id] || id);
                resolved['_originalFocusIds'] = value;
            } else if (key === 'aggregateRules' && Array.isArray(value)) {
                // Recursively resolve nested rules
                resolved[key] = value.map(r => resolveRule(r));
            } else if (key === 'disabledRule' && typeof value === 'object') {
                // Recursively resolve disabled rules
                resolved[key] = resolveRule(value);
            } else {
                resolved[key] = value;
            }
        }
        return resolved;
    }

    const rules = customPersp.archivedFilterRules;
    const aggregation = customPersp.archivedTopLevelFilterAggregation;

    const result = {
        perspectiveName: customPersp.name,
        perspectiveId: customPersp.id ? customPersp.id.primaryKey : null,
        aggregation: aggregation,
        aggregationDescription: aggregation === 'all' ? 'Match ALL of the following rules' :
                               aggregation === 'any' ? 'Match ANY of the following rules' :
                               aggregation === 'none' ? 'Match NONE of the following rules' :
                               'No aggregation specified',
        ruleCount: rules ? rules.length : 0,
        rules: resolveIds ? rules.map(r => resolveRule(r)) : rules,
        _rawRules: resolveIds ? rules : undefined
    };

    return JSON.stringify(result, null, 2);

} catch (error) {
    return JSON.stringify({
        error: "Error getting perspective rules: " + error.toString()
    });
}
