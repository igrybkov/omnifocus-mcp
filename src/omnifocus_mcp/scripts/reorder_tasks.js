// Reorder tasks within a project or parent task
// Params:
//   container_id: ID of project or parent task containing the tasks
//   container_type: 'project' or 'task' (default: 'project')
//   mode: 'sort' | 'move' | 'custom' (required)
//
//   For mode='sort':
//     sort_by: 'name' | 'dueDate' | 'deferDate' | 'plannedDate' | 'flagged' | 'estimatedMinutes'
//     sort_order: 'asc' | 'desc' (default: 'asc')
//
//   For mode='move':
//     task_id: ID of task to move
//     position: 'beginning' | 'ending' | 'before' | 'after'
//     reference_task_id: ID of reference task (required for 'before'/'after')
//
//   For mode='custom':
//     task_ids: Array of task IDs in desired order

try {
    var containerId = params.container_id;
    var containerType = params.container_type || 'project';
    var mode = params.mode;

    if (!containerId) {
        return JSON.stringify({ error: "container_id is required" });
    }
    if (!mode) {
        return JSON.stringify({ error: "mode is required (sort, move, or custom)" });
    }

    // Find the container (project or task)
    var container = null;
    if (containerType === 'project') {
        flattenedProjects.forEach(function(p) {
            if (p.id && p.id.primaryKey === containerId) {
                container = p;
            }
        });
        if (!container) {
            return JSON.stringify({ error: "Project not found with ID: " + containerId });
        }
    } else {
        flattenedTasks.forEach(function(t) {
            if (t.id && t.id.primaryKey === containerId) {
                container = t;
            }
        });
        if (!container) {
            return JSON.stringify({ error: "Task not found with ID: " + containerId });
        }
    }

    // Get direct children only (not flattened)
    var tasks = [];
    container.children.forEach(function(child) {
        if (child instanceof Task) {
            tasks.push(child);
        }
    });

    if (tasks.length === 0) {
        return JSON.stringify({
            success: true,
            message: "No tasks to reorder",
            taskCount: 0
        });
    }

    if (mode === 'sort') {
        var sortBy = params.sort_by || 'name';
        var sortOrder = params.sort_order || 'asc';
        var ascending = sortOrder === 'asc';

        // Sort tasks
        tasks.sort(function(a, b) {
            var valA, valB;

            switch (sortBy) {
                case 'name':
                    valA = (a.name || '').toLowerCase();
                    valB = (b.name || '').toLowerCase();
                    break;
                case 'dueDate':
                    valA = a.effectiveDueDate ? a.effectiveDueDate.getTime() : (ascending ? Infinity : -Infinity);
                    valB = b.effectiveDueDate ? b.effectiveDueDate.getTime() : (ascending ? Infinity : -Infinity);
                    break;
                case 'deferDate':
                    valA = a.effectiveDeferDate ? a.effectiveDeferDate.getTime() : (ascending ? Infinity : -Infinity);
                    valB = b.effectiveDeferDate ? b.effectiveDeferDate.getTime() : (ascending ? Infinity : -Infinity);
                    break;
                case 'plannedDate':
                    valA = a.effectivePlannedDate ? a.effectivePlannedDate.getTime() : (ascending ? Infinity : -Infinity);
                    valB = b.effectivePlannedDate ? b.effectivePlannedDate.getTime() : (ascending ? Infinity : -Infinity);
                    break;
                case 'flagged':
                    // Flagged items first when ascending
                    valA = a.flagged ? 0 : 1;
                    valB = b.flagged ? 0 : 1;
                    break;
                case 'estimatedMinutes':
                    valA = a.estimatedMinutes || (ascending ? Infinity : -Infinity);
                    valB = b.estimatedMinutes || (ascending ? Infinity : -Infinity);
                    break;
                default:
                    return JSON.stringify({ error: "Unknown sort_by: " + sortBy });
            }

            if (valA < valB) return ascending ? -1 : 1;
            if (valA > valB) return ascending ? 1 : -1;
            return 0;
        });

        // Move tasks to new order
        moveTasks(tasks, container.beginning);

        return JSON.stringify({
            success: true,
            message: "Sorted " + tasks.length + " tasks by " + sortBy + " (" + sortOrder + ")",
            taskCount: tasks.length
        });

    } else if (mode === 'move') {
        var taskId = params.task_id;
        var position = params.position;
        var refTaskId = params.reference_task_id;

        if (!taskId) {
            return JSON.stringify({ error: "task_id is required for move mode" });
        }
        if (!position) {
            return JSON.stringify({ error: "position is required for move mode (beginning, ending, before, after)" });
        }

        // Find the task to move
        var taskToMove = null;
        tasks.forEach(function(t) {
            if (t.id && t.id.primaryKey === taskId) {
                taskToMove = t;
            }
        });

        if (!taskToMove) {
            return JSON.stringify({ error: "Task not found in container: " + taskId });
        }

        var destination;
        if (position === 'beginning') {
            destination = container.beginning;
        } else if (position === 'ending') {
            destination = container.ending;
        } else if (position === 'before' || position === 'after') {
            if (!refTaskId) {
                return JSON.stringify({ error: "reference_task_id is required for before/after positioning" });
            }

            var refTask = null;
            tasks.forEach(function(t) {
                if (t.id && t.id.primaryKey === refTaskId) {
                    refTask = t;
                }
            });

            if (!refTask) {
                return JSON.stringify({ error: "Reference task not found: " + refTaskId });
            }

            destination = position === 'before' ? refTask.before : refTask.after;
        } else {
            return JSON.stringify({ error: "Invalid position: " + position });
        }

        moveTasks([taskToMove], destination);

        return JSON.stringify({
            success: true,
            message: "Moved task to " + position,
            taskId: taskId
        });

    } else if (mode === 'custom') {
        var taskIds = params.task_ids;

        if (!taskIds || !Array.isArray(taskIds) || taskIds.length === 0) {
            return JSON.stringify({ error: "task_ids array is required for custom mode" });
        }

        // Build a map of ID to task
        var taskMap = {};
        tasks.forEach(function(t) {
            if (t.id) {
                taskMap[t.id.primaryKey] = t;
            }
        });

        // Validate all IDs exist
        var orderedTasks = [];
        for (var i = 0; i < taskIds.length; i++) {
            var tid = taskIds[i];
            if (!taskMap[tid]) {
                return JSON.stringify({ error: "Task not found in container: " + tid });
            }
            orderedTasks.push(taskMap[tid]);
        }

        // Move tasks in the specified order
        moveTasks(orderedTasks, container.beginning);

        return JSON.stringify({
            success: true,
            message: "Reordered " + orderedTasks.length + " tasks in custom order",
            taskCount: orderedTasks.length
        });

    } else {
        return JSON.stringify({ error: "Unknown mode: " + mode + " (use sort, move, or custom)" });
    }

} catch (error) {
    return JSON.stringify({
        error: "Error reordering tasks: " + error.toString()
    });
}
