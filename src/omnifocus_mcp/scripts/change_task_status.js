// Change a task's status (completed, dropped, incomplete)
// Works for all task types including inbox tasks.
// Params:
//   task_id: ID of the task to change (required)
//   status: Target status - "completed", "dropped", or "incomplete" (required)

try {
    var taskId = params.task_id;
    var status = params.status;

    if (!taskId) {
        return JSON.stringify({ error: "task_id is required" });
    }
    if (!status) {
        return JSON.stringify({ error: "status is required" });
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

    // Apply status change
    if (status === "completed") {
        task.markComplete();
    } else if (status === "dropped") {
        task.drop(true);
    } else if (status === "incomplete") {
        task.markIncomplete();
        task.drop(false);
    } else {
        return JSON.stringify({ error: "Invalid status: " + status + ". Must be completed, dropped, or incomplete" });
    }

    return JSON.stringify({
        success: true,
        message: "Task status changed to " + status,
        taskId: taskId
    });

} catch (error) {
    return JSON.stringify({
        error: "Error changing task status: " + error.toString()
    });
}
