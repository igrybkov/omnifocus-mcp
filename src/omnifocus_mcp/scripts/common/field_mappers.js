// Field mapping functions for OmniFocus items
// Shared between search.js and browse.js
// Requires: status_maps.js to be loaded first

/**
 * Get the folder path for an item (task or project).
 * Returns an array of folder names from root to immediate parent.
 * @param {Object} item - Task or project with folder hierarchy
 * @returns {Array<string>} Array of folder names
 */
function getFolderPath(item) {
    var path = [];
    var folder = null;

    // For tasks, get containing project's folder
    if (item.containingProject) {
        folder = item.containingProject.folder;
    } else if (item.folder) {
        // For projects, get folder directly
        folder = item.folder;
    }

    // Walk up the folder hierarchy
    while (folder) {
        path.unshift(folder.name);
        folder = folder.parent;
    }

    return path;
}

/**
 * Map task fields to output format.
 * @param {Object} task - OmniFocus task object
 * @param {Array<string>} fields - Fields to include (empty = all)
 * @returns {Object} Mapped task object
 */
function mapTaskFields(task, fields) {
    var allFields = {
        id: task.id.primaryKey,
        name: task.name,
        note: task.note || "",
        flagged: task.flagged || false,
        completed: task.completed || false,
        taskStatus: taskStatusMap[task.taskStatus] || "Unknown",
        dueDate: task.dueDate ? task.dueDate.toISOString() : null,
        deferDate: task.deferDate ? task.deferDate.toISOString() : null,
        plannedDate: task.plannedDate ? task.plannedDate.toISOString() : null,
        effectiveDueDate: task.effectiveDueDate ? task.effectiveDueDate.toISOString() : null,
        effectiveDeferDate: task.effectiveDeferDate ? task.effectiveDeferDate.toISOString() : null,
        effectivePlannedDate: task.effectivePlannedDate ? task.effectivePlannedDate.toISOString() : null,
        completionDate: task.completionDate ? task.completionDate.toISOString() : null,
        estimatedMinutes: task.estimatedMinutes || null,
        tagNames: task.tags ? task.tags.map(function(t) { return t.name; }) : [],
        projectName: task.containingProject ? task.containingProject.name : "Inbox",
        projectId: task.containingProject ? task.containingProject.id.primaryKey : null,
        folderPath: getFolderPath(task),
        parentId: task.parent ? task.parent.id.primaryKey : null,
        hasChildren: task.children && task.children.length > 0,
        inInbox: task.inInbox || false,
        modificationDate: task.modificationDate ? task.modificationDate.toISOString() : null,
        creationDate: task.creationDate ? task.creationDate.toISOString() : null
    };

    // If no specific fields requested, return all
    if (!fields || fields.length === 0) {
        return allFields;
    }

    // Return only requested fields
    var result = {};
    for (var i = 0; i < fields.length; i++) {
        var field = fields[i];
        // Handle aliases
        if (field === "modified") field = "modificationDate";
        if (field === "added") field = "creationDate";
        if (field === "status") field = "taskStatus";

        if (field in allFields) {
            result[field] = allFields[field];
        }
    }
    return result;
}

/**
 * Map project fields to output format.
 * @param {Object} project - OmniFocus project object
 * @param {Array<string>} fields - Fields to include (empty = all)
 * @returns {Object} Mapped project object
 */
function mapProjectFields(project, fields) {
    var allFields = {
        id: project.id.primaryKey,
        name: project.name,
        note: project.note || "",
        status: projectStatusMap[project.status] || "Unknown",
        sequential: project.sequential || false,
        flagged: project.flagged || false,
        dueDate: project.dueDate ? project.dueDate.toISOString() : null,
        deferDate: project.deferDate ? project.deferDate.toISOString() : null,
        estimatedMinutes: project.estimatedMinutes || null,
        taskCount: project.flattenedTasks ? project.flattenedTasks.length : 0,
        tagNames: project.tags ? project.tags.map(function(t) { return t.name; }) : [],
        folderName: project.folder ? project.folder.name : null,
        folderId: project.folder ? project.folder.id.primaryKey : null,
        folderPath: getFolderPath(project),
        modificationDate: project.modificationDate ? project.modificationDate.toISOString() : null,
        creationDate: project.creationDate ? project.creationDate.toISOString() : null
    };

    // If no specific fields requested, return all
    if (!fields || fields.length === 0) {
        return allFields;
    }

    // Return only requested fields
    var result = {};
    for (var i = 0; i < fields.length; i++) {
        var field = fields[i];
        // Handle aliases
        if (field === "modified") field = "modificationDate";
        if (field === "added") field = "creationDate";

        if (field in allFields) {
            result[field] = allFields[field];
        }
    }
    return result;
}

/**
 * Map folder fields to output format.
 * @param {Object} folder - OmniFocus folder object
 * @param {Array<string>} fields - Fields to include (empty = all)
 * @returns {Object} Mapped folder object
 */
function mapFolderFields(folder, fields) {
    var allFields = {
        id: folder.id.primaryKey,
        name: folder.name,
        projectCount: folder.flattenedProjects ? folder.flattenedProjects.length : 0,
        folderPath: getFolderPath(folder)
    };

    // If no specific fields requested, return all
    if (!fields || fields.length === 0) {
        return allFields;
    }

    // Return only requested fields
    var result = {};
    for (var i = 0; i < fields.length; i++) {
        var field = fields[i];
        if (field in allFields) {
            result[field] = allFields[field];
        }
    }
    return result;
}
