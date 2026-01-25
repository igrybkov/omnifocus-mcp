// Query OmniFocus database with powerful filters
// Params: {
//   entity: string ('tasks' | 'projects' | 'folders'),
//   filters: object,
//   fields: string[] | null,
//   limit: number | null,
//   sort_by: string | null,
//   sort_order: string ('asc' | 'desc'),
//   include_completed: boolean,
//   summary: boolean
// }

try {
    // Status mappings
    const taskStatusMap = {};
    taskStatusMap[Task.Status.Available] = "Available";
    taskStatusMap[Task.Status.Blocked] = "Blocked";
    taskStatusMap[Task.Status.Completed] = "Completed";
    taskStatusMap[Task.Status.Dropped] = "Dropped";
    taskStatusMap[Task.Status.DueSoon] = "DueSoon";
    taskStatusMap[Task.Status.Next] = "Next";
    taskStatusMap[Task.Status.Overdue] = "Overdue";

    const projectStatusMap = {};
    projectStatusMap[Project.Status.Active] = "Active";
    projectStatusMap[Project.Status.Done] = "Done";
    projectStatusMap[Project.Status.Dropped] = "Dropped";
    projectStatusMap[Project.Status.OnHold] = "OnHold";

    const entityType = params.entity;
    const filters = params.filters || {};
    const requestedFields = params.fields;
    const limit = params.limit;
    const sortBy = params.sort_by;
    const sortOrder = params.sort_order;
    const includeCompleted = params.include_completed;
    const summaryOnly = params.summary;

    // Determine default fields based on entity type
    function getDefaultFields() {
        if (entityType === "tasks") {
            return ["id", "name", "taskStatus", "flagged", "dueDate", "deferDate", "projectName", "tagNames"];
        } else if (entityType === "projects") {
            return ["id", "name", "status", "sequential", "dueDate", "deferDate", "folderName", "taskCount"];
        } else {
            return ["id", "name", "projectCount"];
        }
    }

    const fieldsToInclude = requestedFields || getDefaultFields();

    // Filter function that interprets the filter spec
    function passesFilter(item) {
        // Completed/dropped filter
        if (!includeCompleted) {
            if (entityType === "tasks") {
                if (item.taskStatus === Task.Status.Completed ||
                    item.taskStatus === Task.Status.Dropped) {
                    return false;
                }
            } else if (entityType === "projects") {
                if (item.status === Project.Status.Done ||
                    item.status === Project.Status.Dropped) {
                    return false;
                }
            }
        }

        // Filter by project_id (for tasks)
        if (filters.project_id !== undefined) {
            if (!item.containingProject || item.containingProject.id.primaryKey !== filters.project_id) {
                return false;
            }
        }

        // Filter by project_name (for tasks)
        if (filters.project_name !== undefined) {
            const projectNameLower = filters.project_name.toLowerCase();
            if (item.containingProject) {
                const projectName = item.containingProject.name.toLowerCase();
                if (!projectName.includes(projectNameLower)) {
                    return false;
                }
            } else if (projectNameLower !== "inbox") {
                return false;
            }
        }

        // Filter by folder_id (for projects)
        if (filters.folder_id !== undefined) {
            if (!item.folder || item.folder.id.primaryKey !== filters.folder_id) {
                return false;
            }
        }

        // Filter by tags (OR logic)
        if (filters.tags !== undefined && filters.tags.length > 0) {
            const itemTagNames = item.tags ? item.tags.map(t => t.name) : [];
            if (!filters.tags.some(ft => itemTagNames.includes(ft))) {
                return false;
            }
        }

        // Filter by status
        if (filters.status !== undefined && filters.status.length > 0) {
            const itemStatus = taskStatusMap[item.taskStatus];
            if (!filters.status.includes(itemStatus)) {
                return false;
            }
        }

        // Filter by flagged
        if (filters.flagged !== undefined) {
            if (item.flagged !== filters.flagged) {
                return false;
            }
        }

        // Filter by due_within N days
        if (filters.due_within !== undefined) {
            if (!item.dueDate) {
                return false;
            }
            const now = new Date();
            const futureDate = new Date();
            futureDate.setDate(futureDate.getDate() + filters.due_within);
            if (item.dueDate > futureDate || item.dueDate < now) {
                return false;
            }
        }

        // Filter by deferred_until N days
        if (filters.deferred_until !== undefined) {
            if (!item.deferDate) {
                return false;
            }
            const now = new Date();
            const futureDate = new Date();
            futureDate.setDate(futureDate.getDate() + filters.deferred_until);
            if (item.deferDate > futureDate) {
                return false;
            }
        }

        // Filter by planned_within N days (OmniFocus 4.7+)
        if (filters.planned_within !== undefined) {
            if (!item.plannedDate) {
                return false;
            }
            const now = new Date();
            const futureDate = new Date();
            futureDate.setDate(futureDate.getDate() + filters.planned_within);
            if (item.plannedDate > futureDate || item.plannedDate < now) {
                return false;
            }
        }

        // Filter by has_note
        if (filters.has_note !== undefined) {
            const hasNote = item.note && item.note.trim() !== "";
            if (filters.has_note !== hasNote) {
                return false;
            }
        }

        return true;
    }

    // Map item to output format based on requested fields
    function mapItem(item) {
        const result = {};

        for (const field of fieldsToInclude) {
            switch (field) {
                case "id":
                    result.id = item.id.primaryKey;
                    break;
                case "name":
                    result.name = item.name;
                    break;
                case "note":
                    result.note = item.note || "";
                    break;
                case "flagged":
                    result.flagged = item.flagged || false;
                    break;
                case "taskStatus":
                    result.taskStatus = taskStatusMap[item.taskStatus] || "Unknown";
                    break;
                case "status":
                    result.status = projectStatusMap[item.status] || "Unknown";
                    break;
                case "dueDate":
                    result.dueDate = item.dueDate ? item.dueDate.toISOString() : null;
                    break;
                case "deferDate":
                    result.deferDate = item.deferDate ? item.deferDate.toISOString() : null;
                    break;
                case "plannedDate":
                    result.plannedDate = item.plannedDate ? item.plannedDate.toISOString() : null;
                    break;
                case "effectiveDueDate":
                    result.effectiveDueDate = item.effectiveDueDate ? item.effectiveDueDate.toISOString() : null;
                    break;
                case "effectiveDeferDate":
                    result.effectiveDeferDate = item.effectiveDeferDate ? item.effectiveDeferDate.toISOString() : null;
                    break;
                case "effectivePlannedDate":
                    result.effectivePlannedDate = item.effectivePlannedDate ? item.effectivePlannedDate.toISOString() : null;
                    break;
                case "completionDate":
                    result.completionDate = item.completionDate ? item.completionDate.toISOString() : null;
                    break;
                case "estimatedMinutes":
                    result.estimatedMinutes = item.estimatedMinutes || null;
                    break;
                case "tagNames":
                    result.tagNames = item.tags ? item.tags.map(t => t.name) : [];
                    break;
                case "projectName":
                    result.projectName = item.containingProject ? item.containingProject.name : "Inbox";
                    break;
                case "projectId":
                    result.projectId = item.containingProject ? item.containingProject.id.primaryKey : null;
                    break;
                case "folderName":
                    result.folderName = item.folder ? item.folder.name : null;
                    break;
                case "folderId":
                    result.folderId = item.folder ? item.folder.id.primaryKey : null;
                    break;
                case "sequential":
                    result.sequential = item.sequential || false;
                    break;
                case "taskCount":
                    result.taskCount = item.flattenedTasks ? item.flattenedTasks.length : 0;
                    break;
                case "projectCount":
                    result.projectCount = item.flattenedProjects ? item.flattenedProjects.length : 0;
                    break;
                case "parentId":
                    result.parentId = item.parent ? item.parent.id.primaryKey : null;
                    break;
                case "hasChildren":
                    result.hasChildren = item.children && item.children.length > 0;
                    break;
                case "inInbox":
                    result.inInbox = item.inInbox || false;
                    break;
                case "modificationDate":
                case "modified":
                    result.modificationDate = item.modificationDate ? item.modificationDate.toISOString() : null;
                    break;
                case "creationDate":
                case "added":
                    result.creationDate = item.creationDate ? item.creationDate.toISOString() : null;
                    break;
            }
        }

        return result;
    }

    // Get items based on entity type
    let items = [];
    if (entityType === "tasks") {
        items = flattenedTasks;
    } else if (entityType === "projects") {
        items = flattenedProjects;
    } else if (entityType === "folders") {
        items = flattenedFolders;
    }

    // Filter items
    let filtered = items.filter(passesFilter);

    // Sort if requested
    if (sortBy) {
        const sortDirection = sortOrder === "desc" ? -1 : 1;
        filtered.sort((a, b) => {
            let aVal = a[sortBy];
            let bVal = b[sortBy];

            // Handle dates
            if (aVal instanceof Date) aVal = aVal.getTime();
            if (bVal instanceof Date) bVal = bVal.getTime();

            // Handle nulls
            if (aVal === null || aVal === undefined) return 1;
            if (bVal === null || bVal === undefined) return -1;

            // Compare
            if (aVal < bVal) return -sortDirection;
            if (aVal > bVal) return sortDirection;
            return 0;
        });
    }

    // Limit if requested
    if (limit) {
        filtered = filtered.slice(0, limit);
    }

    // Return summary if requested
    if (summaryOnly) {
        return JSON.stringify({
            count: filtered.length,
            entity: entityType
        });
    }

    // Map to output format
    const results = filtered.map(mapItem);

    return JSON.stringify({
        count: results.length,
        entity: entityType,
        items: results
    });

} catch (error) {
    return JSON.stringify({
        error: "Query error: " + error.toString()
    });
}
