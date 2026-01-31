// Move a task to a new parent (task or project)
// Params:
//   task_id: ID of the task to move (required)
//   new_parent_id: ID of the new parent task or project (required, empty string to un-nest)

try {
    var taskId = params.task_id;
    var newParentId = params.new_parent_id;

    if (!taskId) {
        return JSON.stringify({ error: "task_id is required" });
    }
    if (newParentId === undefined || newParentId === null) {
        return JSON.stringify({ error: "new_parent_id is required (use empty string to un-nest)" });
    }

    // Find the task to move
    var task = null;
    flattenedTasks.forEach(function(t) {
        if (t.id && t.id.primaryKey === taskId) {
            task = t;
        }
    });

    if (!task) {
        return JSON.stringify({ error: "Task not found: " + taskId });
    }

    // Handle un-nesting (moving to project root)
    if (newParentId === "") {
        // Find the containing project
        var containingProject = task.containingProject;
        if (!containingProject) {
            return JSON.stringify({ error: "Task is not in a project (cannot un-nest inbox tasks)" });
        }

        // Check if task is already at project root
        if (task.parent === containingProject) {
            return JSON.stringify({
                success: true,
                message: "Task is already at project root",
                taskId: taskId
            });
        }

        // Move to end of project
        moveTasks([task], containingProject.ending);

        return JSON.stringify({
            success: true,
            message: "Task moved to project root",
            taskId: taskId,
            newParentId: containingProject.id.primaryKey,
            newParentName: containingProject.name
        });
    }

    // Find the new parent (could be a task or project)
    var newParent = null;
    var parentType = null;

    // First check projects
    flattenedProjects.forEach(function(p) {
        if (p.id && p.id.primaryKey === newParentId) {
            newParent = p;
            parentType = "project";
        }
    });

    // If not found in projects, check tasks
    if (!newParent) {
        flattenedTasks.forEach(function(t) {
            if (t.id && t.id.primaryKey === newParentId) {
                newParent = t;
                parentType = "task";
            }
        });
    }

    if (!newParent) {
        return JSON.stringify({ error: "Parent not found: " + newParentId });
    }

    // Prevent moving a task to itself
    if (taskId === newParentId) {
        return JSON.stringify({ error: "Cannot move a task to itself" });
    }

    // Prevent moving a task to one of its own descendants
    if (parentType === "task") {
        var ancestor = newParent.parent;
        while (ancestor) {
            if (ancestor.id && ancestor.id.primaryKey === taskId) {
                return JSON.stringify({ error: "Cannot move a task to one of its descendants" });
            }
            ancestor = ancestor.parent;
        }
    }

    // Move the task to the new parent
    moveTasks([task], newParent.ending);

    return JSON.stringify({
        success: true,
        message: "Task moved to " + parentType + ": " + newParent.name,
        taskId: taskId,
        newParentId: newParentId,
        newParentName: newParent.name,
        newParentType: parentType
    });

} catch (error) {
    return JSON.stringify({
        error: "Error moving task to parent: " + error.toString()
    });
}
