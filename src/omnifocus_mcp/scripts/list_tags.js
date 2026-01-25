// List all tags in OmniFocus
// Params: { include_nested: boolean, include_counts: boolean }

try {
    var includeNested = params.include_nested !== false;
    var includeCounts = params.include_counts !== false;

    // Function to count active tasks for a tag
    function countActiveTasks(tag) {
        if (!includeCounts) return undefined;
        var count = 0;
        tag.tasks.forEach(function(task) {
            if (task.taskStatus === Task.Status.Available ||
                task.taskStatus === Task.Status.DueSoon ||
                task.taskStatus === Task.Status.Blocked ||
                task.taskStatus === Task.Status.Next) {
                count++;
            }
        });
        return count;
    }

    // Function to process a tag and its children
    function processTag(tag, parentName) {
        var tagData = {
            id: tag.id ? tag.id.primaryKey : null,
            name: tag.name,
            parent: parentName || null,
            allowsNextAction: tag.allowsNextAction
        };

        if (includeCounts) {
            tagData.activeTaskCount = countActiveTasks(tag);
        }

        if (includeNested && tag.tags && tag.tags.length > 0) {
            tagData.children = [];
            tag.tags.forEach(function(childTag) {
                tagData.children.push(processTag(childTag, tag.name));
            });
        }

        return tagData;
    }

    // Get all top-level tags
    var result = [];
    var totalCount = 0;

    // Use flattenedTags for counting, but process from top-level for hierarchy
    if (includeNested) {
        // Process hierarchically from top-level tags
        tags.forEach(function(tag) {
            result.push(processTag(tag, null));
        });
        // Count all tags (flattened)
        totalCount = flattenedTags.length;
    } else {
        // Only top-level tags
        tags.forEach(function(tag) {
            result.push(processTag(tag, null));
        });
        totalCount = result.length;
    }

    return JSON.stringify({
        total: totalCount,
        tags: result
    });

} catch (error) {
    return JSON.stringify({
        error: "Error listing tags: " + error.toString()
    });
}
