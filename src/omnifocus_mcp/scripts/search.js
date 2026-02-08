// Search OmniFocus database with powerful filters and aggregation
// Requires: common/status_maps.js, common/filters.js, common/field_mappers.js
// Params: {
//   entity: string ('tasks' | 'projects' | 'folders'),
//   filters: object,
//   group_by: string | null (field to group by),
//   aggregations: object | null (aggregations to compute per group),
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
            return ["id", "name", "note", "taskStatus", "flagged", "dueDate", "deferDate", "projectName", "tagNames"];
        } else if (entityType === "projects") {
            return ["id", "name", "note", "status", "sequential", "dueDate", "deferDate", "folderName", "taskCount"];
        } else {
            return ["id", "name", "projectCount"];
        }
    }

    var fieldsToInclude = requestedFields || getDefaultFields();

    // Build project-to-folder mapping (OmniJS doesn't expose project.folder)
    var projectToFolder = {};
    if (entityType === "projects") {
        function mapProjectsInFolder(folder) {
            if (folder.projects) {
                for (var i = 0; i < folder.projects.length; i++) {
                    var proj = folder.projects[i];
                    var folderPath = [];
                    var currentFolder = folder;
                    while (currentFolder) {
                        folderPath.unshift(currentFolder.name);
                        currentFolder = currentFolder.parent;
                    }
                    projectToFolder[proj.id.primaryKey] = {
                        folderId: folder.id.primaryKey,
                        folderName: folder.name,
                        folderPath: folderPath
                    };
                }
            }
            if (folder.folders) {
                for (var j = 0; j < folder.folders.length; j++) {
                    mapProjectsInFolder(folder.folders[j]);
                }
            }
        }
        var allFolders = flattenedFolders;
        for (var i = 0; i < allFolders.length; i++) {
            mapProjectsInFolder(allFolders[i]);
        }
    }

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

    // Helper function to map item to output format
    function mapItemToOutput(item) {
        if (entityType === "tasks") {
            return mapTaskFields(item, fieldsToInclude);
        } else if (entityType === "projects") {
            var result = mapProjectFields(item, fieldsToInclude);
            // Override folder fields with our mapping (OmniJS doesn't expose project.folder)
            var folderInfo = projectToFolder[item.id.primaryKey];
            if (folderInfo) {
                result.folderName = folderInfo.folderName;
                result.folderId = folderInfo.folderId;
                result.folderPath = folderInfo.folderPath;
            }
            return result;
        } else {
            return mapFolderFields(item, fieldsToInclude);
        }
    }

    // Helper function to create a filter from aggregation filter spec
    function createFilterFromAggregation(filterSpec) {
        return function(item) {
            // Create appropriate filter function based on entity type
            var filterFn;
            if (entityType === "tasks") {
                filterFn = createTaskFilter(filterSpec, { includeCompleted: true });
            } else if (entityType === "projects") {
                filterFn = createProjectFilter(filterSpec, { includeCompleted: true });
            } else {
                filterFn = function() { return true; };
            }
            return filterFn(item);
        };
    }

    // Helper function to aggregate results
    function aggregateResults(items, groupBy, aggregations, fieldsToInclude) {
        // Group items by the specified field
        var groups = {};
        for (var i = 0; i < items.length; i++) {
            var item = items[i];
            var groupKey = getGroupKey(item, groupBy, entityType);

            // Handle null/undefined grouping keys
            if (groupKey === null || groupKey === undefined) {
                groupKey = "(none)";
            } else {
                // Convert to string for consistent grouping
                groupKey = String(groupKey);
            }

            if (!groups[groupKey]) {
                groups[groupKey] = [];
            }
            groups[groupKey].push(item);
        }

        // Apply aggregations to each group
        var results = [];
        for (var key in groups) {
            var group = groups[key];
            var result = {};
            result[groupBy] = key === "(none)" ? null : key;

            // Process each aggregation
            for (var aggName in aggregations) {
                var agg = aggregations[aggName];

                if (agg === "count") {
                    result[aggName] = group.length;
                } else if (typeof agg === "object") {
                    // Nested aggregation or filtered count
                    if (agg.group_by) {
                        // Recursive nested grouping
                        result[aggName] = aggregateResults(group, agg.group_by, agg, fieldsToInclude);
                    } else if (agg.filter) {
                        // Filtered count
                        var filtered = group.filter(createFilterFromAggregation(agg.filter));
                        if (agg.aggregate === "count") {
                            result[aggName] = filtered.length;
                        } else {
                            result[aggName] = filtered.length;  // Default to count
                        }
                    } else if (agg.include_examples) {
                        // Include sample items
                        var exampleFields = agg.example_fields || fieldsToInclude;
                        result[aggName] = group.slice(0, agg.include_examples).map(function(item) {
                            return mapItemToOutput(item);
                        });
                    }
                }
            }

            results.push(result);
        }

        return results;
    }

    // Apply aggregation if requested
    if (params.group_by) {
        var aggregatedResults = aggregateResults(
            filtered,
            params.group_by,
            params.aggregations || {"count": "count"},
            fieldsToInclude
        );
        return JSON.stringify({
            entity: entityType,
            groupedBy: params.group_by,
            groups: aggregatedResults
        });
    }

    // Map to output format using shared field mappers (non-aggregated)
    var results = filtered.map(mapItemToOutput);

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
