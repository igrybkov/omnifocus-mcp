// Move a task to a specific position within its container
// Params:
//   task_id: ID of the task to move (required)
//   position: 'beginning' | 'ending' | 'before' | 'after' (required)
//   reference_task_id: ID of reference task (required for 'before'/'after')

try {
    var taskId = params.task_id;
    var position = params.position;
    var refTaskId = params.reference_task_id;

    if (!taskId) {
        return JSON.stringify({ error: "task_id is required" });
    }
    if (!position) {
        return JSON.stringify({ error: "position is required (beginning, ending, before, after)" });
    }

    // Find the task
    var task = null;
    flattenedTasks.forEach(function(t) {
        if (t.id && t.id.primaryKey === taskId) {
            task = t;
        }
    });

    if (!task) {
        return JSON.stringify({ error: "Task not found: " + taskId });
    }

    // Get the container (parent task or project)
    var container = task.parent;
    if (!container) {
        return JSON.stringify({ error: "Task has no container (inbox tasks cannot be reordered)" });
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

        // Find the reference task
        var refTask = null;
        flattenedTasks.forEach(function(t) {
            if (t.id && t.id.primaryKey === refTaskId) {
                refTask = t;
            }
        });

        if (!refTask) {
            return JSON.stringify({ error: "Reference task not found: " + refTaskId });
        }

        // Verify reference task is in the same container
        if (refTask.parent !== container) {
            return JSON.stringify({ error: "Reference task is not in the same container" });
        }

        destination = position === 'before' ? refTask.before : refTask.after;
    } else {
        return JSON.stringify({ error: "Invalid position: " + position + " (use beginning, ending, before, after)" });
    }

    moveTasks([task], destination);

    return JSON.stringify({
        success: true,
        message: "Task moved to " + position,
        taskId: taskId
    });

} catch (error) {
    return JSON.stringify({
        error: "Error moving task: " + error.toString()
    });
}
