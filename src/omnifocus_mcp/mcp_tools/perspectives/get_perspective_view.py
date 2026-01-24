"""Get perspective view tool for OmniFocus."""

import json
from typing import Optional
from ...omnijs import execute_omnijs


async def get_perspective_view(
    perspective_name: str,
    limit: int = 100,
    include_metadata: bool = True,
    fields: Optional[list[str]] = None,
) -> str:
    """
    Get the items visible in a specific OmniFocus perspective.

    Shows what tasks and projects are displayed when viewing that perspective.

    Args:
        perspective_name: Name of perspective to view (e.g., 'Inbox', 'Projects',
            'Flagged', or a custom perspective name)
        limit: Maximum number of items to return (default: 100)
        include_metadata: Include metadata like project names, tags, dates (default: True)
        fields: Specific fields to include (reduces response size).
            Available: id, name, note, flagged, dueDate, deferDate, completionDate,
            taskStatus, projectName, tagNames, estimatedMinutes

    Returns:
        JSON string with perspective content
    """
    default_fields = ["id", "name", "flagged", "dueDate", "taskStatus", "projectName", "tagNames"]
    fields_to_use = fields if fields else default_fields
    fields_json = json.dumps(fields_to_use)

    script = f'''
    (() => {{
        try {{
            const perspectiveName = "{perspective_name}";
            const limit = {limit};
            const includeMetadata = {str(include_metadata).lower()};
            const fieldsToInclude = {fields_json};

            // Status mapping
            const taskStatusMap = {{}};
            taskStatusMap[Task.Status.Available] = "Available";
            taskStatusMap[Task.Status.Blocked] = "Blocked";
            taskStatusMap[Task.Status.Completed] = "Completed";
            taskStatusMap[Task.Status.Dropped] = "Dropped";
            taskStatusMap[Task.Status.DueSoon] = "DueSoon";
            taskStatusMap[Task.Status.Next] = "Next";
            taskStatusMap[Task.Status.Overdue] = "Overdue";

            // Helper to get task details
            function getTaskDetails(task) {{
                const result = {{}};

                for (const field of fieldsToInclude) {{
                    switch (field) {{
                        case "id":
                            result.id = task.id.primaryKey;
                            break;
                        case "name":
                            result.name = task.name;
                            break;
                        case "note":
                            result.note = task.note || "";
                            break;
                        case "flagged":
                            result.flagged = task.flagged || false;
                            break;
                        case "dueDate":
                            result.dueDate = task.dueDate ? task.dueDate.toISOString() : null;
                            break;
                        case "deferDate":
                            result.deferDate = task.deferDate ? task.deferDate.toISOString() : null;
                            break;
                        case "completionDate":
                            result.completionDate = task.completionDate ? task.completionDate.toISOString() : null;
                            break;
                        case "taskStatus":
                            result.taskStatus = taskStatusMap[task.taskStatus] || "Unknown";
                            break;
                        case "projectName":
                            result.projectName = task.containingProject ? task.containingProject.name : "Inbox";
                            break;
                        case "tagNames":
                            result.tagNames = task.tags ? task.tags.map(t => t.name) : [];
                            break;
                        case "estimatedMinutes":
                            result.estimatedMinutes = task.estimatedMinutes || null;
                            break;
                    }}
                }}

                return result;
            }}

            let items = [];
            const normalizedName = perspectiveName.toLowerCase();

            // Handle built-in perspectives
            if (normalizedName === "inbox") {{
                inbox.forEach(task => {{
                    if (items.length < limit) {{
                        items.push(getTaskDetails(task));
                    }}
                }});
            }} else if (normalizedName === "projects") {{
                flattenedProjects.forEach(project => {{
                    if (items.length < limit && project.status === Project.Status.Active) {{
                        items.push({{
                            id: project.id.primaryKey,
                            name: project.name,
                            type: "project",
                            taskCount: project.flattenedTasks ? project.flattenedTasks.length : 0,
                            status: "Active"
                        }});
                    }}
                }});
            }} else if (normalizedName === "tags") {{
                // Show tasks grouped by tag - just return all tagged tasks
                const seenIds = new Set();
                flattenedTags.forEach(tag => {{
                    tag.remainingTasks.forEach(task => {{
                        const taskId = task.id.primaryKey;
                        if (items.length < limit && !seenIds.has(taskId)) {{
                            seenIds.add(taskId);
                            items.push(getTaskDetails(task));
                        }}
                    }});
                }});
            }} else if (normalizedName === "flagged") {{
                flattenedTasks.forEach(task => {{
                    if (items.length < limit && task.flagged &&
                        task.taskStatus !== Task.Status.Completed &&
                        task.taskStatus !== Task.Status.Dropped) {{
                        items.push(getTaskDetails(task));
                    }}
                }});
            }} else if (normalizedName === "forecast") {{
                // Forecast shows items due soon or deferred until today
                const today = new Date();
                const weekFromNow = new Date();
                weekFromNow.setDate(weekFromNow.getDate() + 7);

                flattenedTasks.forEach(task => {{
                    if (items.length < limit &&
                        task.taskStatus !== Task.Status.Completed &&
                        task.taskStatus !== Task.Status.Dropped) {{
                        if (task.dueDate && task.dueDate <= weekFromNow) {{
                            items.push(getTaskDetails(task));
                        }} else if (task.deferDate && task.deferDate <= today) {{
                            items.push(getTaskDetails(task));
                        }}
                    }}
                }});
            }} else if (normalizedName === "review") {{
                // Review shows projects due for review
                flattenedProjects.forEach(project => {{
                    if (items.length < limit && project.status === Project.Status.Active) {{
                        // Check if project needs review
                        if (project.nextReviewDate) {{
                            const now = new Date();
                            if (project.nextReviewDate <= now) {{
                                items.push({{
                                    id: project.id.primaryKey,
                                    name: project.name,
                                    type: "project",
                                    nextReviewDate: project.nextReviewDate.toISOString(),
                                    status: "NeedsReview"
                                }});
                            }}
                        }}
                    }}
                }});
            }} else {{
                // Try to find a custom perspective with this name
                try {{
                    const customPerspectives = Perspective.Custom.all;
                    let found = false;

                    for (const perspective of customPerspectives) {{
                        if (perspective.name.toLowerCase() === normalizedName) {{
                            found = true;
                            // Note: OmniJS doesn't provide direct access to perspective contents
                            // We would need to switch to the perspective, which requires UI
                            // Instead, return a message about this limitation
                            break;
                        }}
                    }}

                    if (found) {{
                        return JSON.stringify({{
                            perspectiveName: perspectiveName,
                            type: "custom",
                            note: "Custom perspective found but content cannot be accessed programmatically. " +
                                  "OmniJS cannot switch perspectives without UI interaction.",
                            items: []
                        }});
                    }} else {{
                        return JSON.stringify({{
                            error: "Perspective not found: " + perspectiveName
                        }});
                    }}
                }} catch (e) {{
                    return JSON.stringify({{
                        error: "Error accessing custom perspectives: " + e.toString()
                    }});
                }}
            }}

            return JSON.stringify({{
                perspectiveName: perspectiveName,
                type: "builtin",
                count: items.length,
                items: items
            }});

        }} catch (error) {{
            return JSON.stringify({{
                error: "Error getting perspective view: " + error.toString()
            }});
        }}
    }})();
    '''

    try:
        result = await execute_omnijs(script)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
