"""Database dump tool for OmniFocus."""

import json
from ...omnijs import execute_omnijs


async def dump_database(
    hide_completed: bool = True,
    hide_recurring_duplicates: bool = True,
) -> str:
    """
    Gets the complete current state of your OmniFocus database in a compact, formatted report.

    NOTE: This tool is only available when running with --expanded flag.

    Args:
        hide_completed: Set to False to show completed and dropped tasks (default: True)
        hide_recurring_duplicates: Set to True to hide duplicate instances of
            recurring tasks (default: True)

    Returns:
        Formatted database dump with hierarchical structure
    """
    script = f'''
    (() => {{
        try {{
            const hideCompleted = {str(hide_completed).lower()};
            const hideRecurringDuplicates = {str(hide_recurring_duplicates).lower()};

            // Status mappings
            const taskStatusMap = {{}};
            taskStatusMap[Task.Status.Available] = "avail";
            taskStatusMap[Task.Status.Blocked] = "block";
            taskStatusMap[Task.Status.Completed] = "compl";
            taskStatusMap[Task.Status.Dropped] = "drop";
            taskStatusMap[Task.Status.DueSoon] = "due";
            taskStatusMap[Task.Status.Next] = "next";
            taskStatusMap[Task.Status.Overdue] = "over";

            const projectStatusMap = {{}};
            projectStatusMap[Project.Status.Active] = "active";
            projectStatusMap[Project.Status.Done] = "done";
            projectStatusMap[Project.Status.Dropped] = "dropped";
            projectStatusMap[Project.Status.OnHold] = "onHold";

            // Format date as M/D
            function formatDate(date) {{
                if (!date) return null;
                return (date.getMonth() + 1) + "/" + date.getDate();
            }}

            // Format duration
            function formatDuration(minutes) {{
                if (!minutes) return null;
                if (minutes >= 60) {{
                    return Math.floor(minutes / 60) + "h";
                }}
                return minutes + "m";
            }}

            // Track seen recurring task names to filter duplicates
            const seenRecurring = new Set();

            // Build output
            let output = [];

            // Legend
            output.push("Legend: F:Folder P:Project \\u2022:Task \\uD83D\\uDEA9:Flagged [M/D]:Date <tag>:Tags");
            output.push("Status: #next #avail #block #due #over #compl #drop");
            output.push("");

            // Process folders
            flattenedFolders.forEach(folder => {{
                output.push("F: " + folder.name);

                // Get projects in this folder
                folder.projects.forEach(project => {{
                    if (hideCompleted && (project.status === Project.Status.Done ||
                                          project.status === Project.Status.Dropped)) {{
                        return;
                    }}

                    let projectLine = "  P: " + project.name;
                    if (project.status !== Project.Status.Active) {{
                        projectLine += " #" + projectStatusMap[project.status];
                    }}
                    if (project.dueDate) {{
                        projectLine += " [" + formatDate(project.dueDate) + "]";
                    }}
                    output.push(projectLine);

                    // Get tasks in this project
                    project.flattenedTasks.forEach(task => {{
                        if (hideCompleted && (task.taskStatus === Task.Status.Completed ||
                                              task.taskStatus === Task.Status.Dropped)) {{
                            return;
                        }}

                        // Filter recurring duplicates
                        if (hideRecurringDuplicates && task.repetitionRule) {{
                            const key = task.name + "|" + (task.containingProject ? task.containingProject.name : "");
                            if (seenRecurring.has(key)) {{
                                return;
                            }}
                            seenRecurring.add(key);
                        }}

                        let taskLine = "    \\u2022 " + task.name;

                        // Add status
                        const status = taskStatusMap[task.taskStatus];
                        if (status && status !== "avail") {{
                            taskLine += " #" + status;
                        }}

                        // Add flag
                        if (task.flagged) {{
                            taskLine += " \\uD83D\\uDEA9";
                        }}

                        // Add due date
                        if (task.dueDate) {{
                            taskLine += " [" + formatDate(task.dueDate) + "]";
                        }}

                        // Add duration
                        if (task.estimatedMinutes) {{
                            taskLine += " " + formatDuration(task.estimatedMinutes);
                        }}

                        // Add tags
                        if (task.tags && task.tags.length > 0) {{
                            taskLine += " <" + task.tags.map(t => t.name).join(",") + ">";
                        }}

                        output.push(taskLine);
                    }});
                }});

                output.push("");
            }});

            // Also show projects not in any folder
            flattenedProjects.forEach(project => {{
                if (project.folder) return; // Already shown

                if (hideCompleted && (project.status === Project.Status.Done ||
                                      project.status === Project.Status.Dropped)) {{
                    return;
                }}

                let projectLine = "P: " + project.name;
                if (project.status !== Project.Status.Active) {{
                    projectLine += " #" + projectStatusMap[project.status];
                }}
                if (project.dueDate) {{
                    projectLine += " [" + formatDate(project.dueDate) + "]";
                }}
                output.push(projectLine);

                // Get tasks in this project
                project.flattenedTasks.forEach(task => {{
                    if (hideCompleted && (task.taskStatus === Task.Status.Completed ||
                                          task.taskStatus === Task.Status.Dropped)) {{
                        return;
                    }}

                    if (hideRecurringDuplicates && task.repetitionRule) {{
                        const key = task.name + "|" + project.name;
                        if (seenRecurring.has(key)) {{
                            return;
                        }}
                        seenRecurring.add(key);
                    }}

                    let taskLine = "  \\u2022 " + task.name;

                    const status = taskStatusMap[task.taskStatus];
                    if (status && status !== "avail") {{
                        taskLine += " #" + status;
                    }}

                    if (task.flagged) {{
                        taskLine += " \\uD83D\\uDEA9";
                    }}

                    if (task.dueDate) {{
                        taskLine += " [" + formatDate(task.dueDate) + "]";
                    }}

                    if (task.estimatedMinutes) {{
                        taskLine += " " + formatDuration(task.estimatedMinutes);
                    }}

                    if (task.tags && task.tags.length > 0) {{
                        taskLine += " <" + task.tags.map(t => t.name).join(",") + ">";
                    }}

                    output.push(taskLine);
                }});

                output.push("");
            }});

            // Show inbox tasks
            if (inbox.length > 0) {{
                output.push("INBOX:");
                inbox.forEach(task => {{
                    if (hideCompleted && (task.taskStatus === Task.Status.Completed ||
                                          task.taskStatus === Task.Status.Dropped)) {{
                        return;
                    }}

                    let taskLine = "  \\u2022 " + task.name;

                    const status = taskStatusMap[task.taskStatus];
                    if (status && status !== "avail") {{
                        taskLine += " #" + status;
                    }}

                    if (task.flagged) {{
                        taskLine += " \\uD83D\\uDEA9";
                    }}

                    if (task.dueDate) {{
                        taskLine += " [" + formatDate(task.dueDate) + "]";
                    }}

                    if (task.estimatedMinutes) {{
                        taskLine += " " + formatDuration(task.estimatedMinutes);
                    }}

                    if (task.tags && task.tags.length > 0) {{
                        taskLine += " <" + task.tags.map(t => t.name).join(",") + ">";
                    }}

                    output.push(taskLine);
                }});
            }}

            return output.join("\\n");

        }} catch (error) {{
            return "Error dumping database: " + error.toString();
        }}
    }})();
    '''

    try:
        result = await execute_omnijs(script)
        # The result might be wrapped in quotes from JSON, handle both cases
        if isinstance(result, dict):
            if "error" in result:
                return f"Error: {result['error']}"
            if "result" in result:
                return result["result"]
            return json.dumps(result, indent=2)
        return str(result)
    except Exception as e:
        return f"Error dumping database: {str(e)}"
