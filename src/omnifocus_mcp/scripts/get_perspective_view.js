// Get items visible in a specific OmniFocus perspective
// Params: { perspective_name: string, limit: number, include_metadata: boolean, fields: string[] }
// Requires: common/status_maps.js

try {
    const perspectiveName = params.perspective_name;
    const limit = params.limit;
    const includeMetadata = params.include_metadata;
    const fieldsToInclude = params.fields;

    // Helper to get task details
    function getTaskDetails(task) {
        const result = {};

        for (const field of fieldsToInclude) {
            switch (field) {
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
            }
        }

        return result;
    }

    function getProjectStatus(status) {
        return projectStatusMap[status] || "Unknown";
    }

    let items = [];
    const normalizedName = perspectiveName.toLowerCase();

    // Handle built-in perspectives
    if (normalizedName === "inbox") {
        inbox.forEach(task => {
            if (items.length < limit) {
                items.push(getTaskDetails(task));
            }
        });
    } else if (normalizedName === "projects") {
        flattenedProjects.forEach(project => {
            if (items.length < limit && project.status === Project.Status.Active) {
                items.push({
                    id: project.id.primaryKey,
                    name: project.name,
                    type: "project",
                    taskCount: project.flattenedTasks ? project.flattenedTasks.length : 0,
                    status: "Active"
                });
            }
        });
    } else if (normalizedName === "tags") {
        // Show tasks grouped by tag - just return all tagged tasks
        const seenIds = new Set();
        flattenedTags.forEach(tag => {
            tag.remainingTasks.forEach(task => {
                const taskId = task.id.primaryKey;
                if (items.length < limit && !seenIds.has(taskId)) {
                    seenIds.add(taskId);
                    items.push(getTaskDetails(task));
                }
            });
        });
    } else if (normalizedName === "flagged") {
        flattenedTasks.forEach(task => {
            if (items.length < limit && task.flagged &&
                task.taskStatus !== Task.Status.Completed &&
                task.taskStatus !== Task.Status.Dropped) {
                items.push(getTaskDetails(task));
            }
        });
    } else if (normalizedName === "forecast") {
        // Forecast shows items due soon or deferred until today
        const today = new Date();
        const weekFromNow = new Date();
        weekFromNow.setDate(weekFromNow.getDate() + 7);

        flattenedTasks.forEach(task => {
            if (items.length < limit &&
                task.taskStatus !== Task.Status.Completed &&
                task.taskStatus !== Task.Status.Dropped) {
                if (task.dueDate && task.dueDate <= weekFromNow) {
                    items.push(getTaskDetails(task));
                } else if (task.deferDate && task.deferDate <= today) {
                    items.push(getTaskDetails(task));
                }
            }
        });
    } else if (normalizedName === "review") {
        // Review shows projects due for review
        flattenedProjects.forEach(project => {
            if (items.length < limit && project.status === Project.Status.Active) {
                // Check if project needs review
                if (project.nextReviewDate) {
                    const now = new Date();
                    if (project.nextReviewDate <= now) {
                        items.push({
                            id: project.id.primaryKey,
                            name: project.name,
                            type: "project",
                            nextReviewDate: project.nextReviewDate.toISOString(),
                            status: "NeedsReview"
                        });
                    }
                }
            }
        });
    } else {
        // Custom perspective - use content tree API
        try {
            const customPersp = Perspective.Custom.all.find(
                p => p.name.toLowerCase() === normalizedName
            );

            if (!customPersp) {
                return JSON.stringify({
                    error: "Perspective not found: " + perspectiveName
                });
            }

            // Check for open window (required for content tree access)
            if (!document.windows.length) {
                return JSON.stringify({
                    error: "No OmniFocus window is open. Custom perspectives require an open window."
                });
            }

            const win = document.windows[0];
            const originalPerspective = win.perspective;

            // Switch to custom perspective
            win.perspective = customPersp;

            // Traverse content tree
            const content = win.content;
            if (content && content.rootNode) {
                content.rootNode.apply(node => {
                    if (items.length >= limit) return;
                    if (node.object instanceof Task) {
                        items.push(getTaskDetails(node.object));
                    } else if (node.object instanceof Project) {
                        items.push({
                            id: node.object.id.primaryKey,
                            name: node.object.name,
                            type: "project",
                            status: getProjectStatus(node.object.status)
                        });
                    }
                });
            }

            // Restore original perspective
            win.perspective = originalPerspective;

            return JSON.stringify({
                perspectiveName: perspectiveName,
                type: "custom",
                count: items.length,
                items: items
            });

        } catch (e) {
            return JSON.stringify({
                error: "Error accessing custom perspective: " + e.toString()
            });
        }
    }

    return JSON.stringify({
        perspectiveName: perspectiveName,
        type: "builtin",
        count: items.length,
        items: items
    });

} catch (error) {
    return JSON.stringify({
        error: "Error getting perspective view: " + error.toString()
    });
}
