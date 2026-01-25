// Dump OmniFocus database in a compact, formatted report
// Params: { hide_completed: boolean, hide_recurring_duplicates: boolean }

try {
    const hideCompleted = params.hide_completed;
    const hideRecurringDuplicates = params.hide_recurring_duplicates;

    // Status mappings
    const taskStatusMap = {};
    taskStatusMap[Task.Status.Available] = "avail";
    taskStatusMap[Task.Status.Blocked] = "block";
    taskStatusMap[Task.Status.Completed] = "compl";
    taskStatusMap[Task.Status.Dropped] = "drop";
    taskStatusMap[Task.Status.DueSoon] = "due";
    taskStatusMap[Task.Status.Next] = "next";
    taskStatusMap[Task.Status.Overdue] = "over";

    const projectStatusMap = {};
    projectStatusMap[Project.Status.Active] = "active";
    projectStatusMap[Project.Status.Done] = "done";
    projectStatusMap[Project.Status.Dropped] = "dropped";
    projectStatusMap[Project.Status.OnHold] = "onHold";

    // Format date as M/D
    function formatDate(date) {
        if (!date) return null;
        return (date.getMonth() + 1) + "/" + date.getDate();
    }

    // Format duration
    function formatDuration(minutes) {
        if (!minutes) return null;
        if (minutes >= 60) {
            return Math.floor(minutes / 60) + "h";
        }
        return minutes + "m";
    }

    // Track seen recurring task names to filter duplicates
    const seenRecurring = new Set();

    // Build output
    let output = [];

    // Legend
    output.push("Legend: F:Folder P:Project \u2022:Task \uD83D\uDEA9:Flagged [M/D]:Date <tag>:Tags");
    output.push("Status: #next #avail #block #due #over #compl #drop");
    output.push("");

    // Helper to format a task line
    function formatTaskLine(task, indent) {
        let taskLine = indent + "\u2022 " + task.name;

        // Add status
        const status = taskStatusMap[task.taskStatus];
        if (status && status !== "avail") {
            taskLine += " #" + status;
        }

        // Add flag
        if (task.flagged) {
            taskLine += " \uD83D\uDEA9";
        }

        // Add due date
        if (task.dueDate) {
            taskLine += " [" + formatDate(task.dueDate) + "]";
        }

        // Add duration
        if (task.estimatedMinutes) {
            taskLine += " " + formatDuration(task.estimatedMinutes);
        }

        // Add tags
        if (task.tags && task.tags.length > 0) {
            taskLine += " <" + task.tags.map(t => t.name).join(",") + ">";
        }

        return taskLine;
    }

    // Check if task should be shown
    function shouldShowTask(task, projectName) {
        if (hideCompleted && (task.taskStatus === Task.Status.Completed ||
                              task.taskStatus === Task.Status.Dropped)) {
            return false;
        }

        // Filter recurring duplicates
        if (hideRecurringDuplicates && task.repetitionRule) {
            const key = task.name + "|" + (projectName || "");
            if (seenRecurring.has(key)) {
                return false;
            }
            seenRecurring.add(key);
        }

        return true;
    }

    // Process folders
    flattenedFolders.forEach(folder => {
        output.push("F: " + folder.name);

        // Get projects in this folder
        folder.projects.forEach(project => {
            if (hideCompleted && (project.status === Project.Status.Done ||
                                  project.status === Project.Status.Dropped)) {
                return;
            }

            let projectLine = "  P: " + project.name;
            if (project.status !== Project.Status.Active) {
                projectLine += " #" + projectStatusMap[project.status];
            }
            if (project.dueDate) {
                projectLine += " [" + formatDate(project.dueDate) + "]";
            }
            output.push(projectLine);

            // Get tasks in this project
            project.flattenedTasks.forEach(task => {
                if (shouldShowTask(task, project.name)) {
                    output.push(formatTaskLine(task, "    "));
                }
            });
        });

        output.push("");
    });

    // Also show projects not in any folder
    flattenedProjects.forEach(project => {
        if (project.folder) return; // Already shown

        if (hideCompleted && (project.status === Project.Status.Done ||
                              project.status === Project.Status.Dropped)) {
            return;
        }

        let projectLine = "P: " + project.name;
        if (project.status !== Project.Status.Active) {
            projectLine += " #" + projectStatusMap[project.status];
        }
        if (project.dueDate) {
            projectLine += " [" + formatDate(project.dueDate) + "]";
        }
        output.push(projectLine);

        // Get tasks in this project
        project.flattenedTasks.forEach(task => {
            if (shouldShowTask(task, project.name)) {
                output.push(formatTaskLine(task, "  "));
            }
        });

        output.push("");
    });

    // Show inbox tasks
    if (inbox.length > 0) {
        output.push("INBOX:");
        inbox.forEach(task => {
            if (shouldShowTask(task, null)) {
                output.push(formatTaskLine(task, "  "));
            }
        });
    }

    return output.join("\n");

} catch (error) {
    return "Error dumping database: " + error.toString();
}
