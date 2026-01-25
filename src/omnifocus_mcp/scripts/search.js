// Search OmniFocus database with powerful filters
// Requires: common/status_maps.js, common/filters.js, common/field_mappers.js
// Params: {
//   entity: string ('tasks' | 'projects' | 'folders'),
//   filters: object,
//   fields: string[] | null,
//   limit: number | null,
//   sort_by: string | null,
//   sort_order: string ('asc' | 'desc'),
//   include_completed: boolean,
//   summary: boolean
// }

try {
    var entityType = params.entity;
    var filters = params.filters || {};
    var requestedFields = params.fields;
    var limit = params.limit;
    var sortBy = params.sort_by;
    var sortOrder = params.sort_order;
    var includeCompleted = params.include_completed;
    var summaryOnly = params.summary;

    // Determine default fields based on entity type
    function getDefaultFields() {
        if (entityType === "tasks") {
            return ["id", "name", "taskStatus", "flagged", "dueDate", "deferDate", "projectName", "tagNames"];
        } else if (entityType === "projects") {
            return ["id", "name", "status", "sequential", "dueDate", "deferDate", "folderName", "taskCount"];
        } else {
            return ["id", "name", "projectCount"];
        }
    }

    var fieldsToInclude = requestedFields || getDefaultFields();

    // Get items based on entity type
    var items = [];
    if (entityType === "tasks") {
        items = flattenedTasks;
    } else if (entityType === "projects") {
        items = flattenedProjects;
    } else if (entityType === "folders") {
        items = flattenedFolders;
    }

    // Create filter function based on entity type
    var filterFn;
    if (entityType === "tasks") {
        filterFn = createTaskFilter(filters, { includeCompleted: includeCompleted });
    } else if (entityType === "projects") {
        filterFn = createProjectFilter(filters, { includeCompleted: includeCompleted });
    } else {
        // Folders don't have status filtering
        filterFn = function() { return true; };
    }

    // Filter items
    var filtered = items.filter(filterFn);

    // Sort if requested
    if (sortBy) {
        var sortDirection = sortOrder === "desc" ? -1 : 1;
        filtered.sort(function(a, b) {
            var aVal = a[sortBy];
            var bVal = b[sortBy];

            // Handle dates
            if (aVal instanceof Date) aVal = aVal.getTime();
            if (bVal instanceof Date) bVal = bVal.getTime();

            // Handle nulls
            if (aVal === null || aVal === undefined) return 1;
            if (bVal === null || bVal === undefined) return -1;

            // Compare
            if (aVal < bVal) return -sortDirection;
            if (aVal > bVal) return sortDirection;
            return 0;
        });
    }

    // Limit if requested
    if (limit) {
        filtered = filtered.slice(0, limit);
    }

    // Return summary if requested
    if (summaryOnly) {
        return JSON.stringify({
            count: filtered.length,
            entity: entityType
        });
    }

    // Map to output format using shared field mappers
    var results = filtered.map(function(item) {
        if (entityType === "tasks") {
            return mapTaskFields(item, fieldsToInclude);
        } else if (entityType === "projects") {
            return mapProjectFields(item, fieldsToInclude);
        } else {
            return mapFolderFields(item, fieldsToInclude);
        }
    });

    return JSON.stringify({
        count: results.length,
        entity: entityType,
        items: results
    });

} catch (error) {
    return JSON.stringify({
        error: "Search error: " + error.toString()
    });
}
