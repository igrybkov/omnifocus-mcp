// Filter factory functions for OmniFocus items
// Shared between search.js and browse.js
// Requires: status_maps.js to be loaded first

/**
 * Check if a date falls within N days from now.
 * @param {Date|null} date - The date to check
 * @param {number} days - Number of days in the future
 * @param {boolean} requirePastOrPresent - If true, date must also be >= now (for due dates)
 * @returns {boolean} True if date is within range
 */
function isWithinDays(date, days, requirePastOrPresent) {
    if (!date) {
        return false;
    }
    var now = new Date();
    var futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + days);

    if (date > futureDate) {
        return false;
    }
    if (requirePastOrPresent && date < now) {
        return false;
    }
    return true;
}

/**
 * Create a filter function for tasks.
 * @param {Object} filters - Filter criteria
 * @param {Object} options - Additional options
 * @param {boolean} options.includeCompleted - Include completed/dropped tasks
 * @returns {Function} Filter function for tasks
 */
function createTaskFilter(filters, options) {
    var includeCompleted = options.includeCompleted || false;

    return function(task) {
        // Completed/dropped filter
        if (!includeCompleted) {
            if (task.taskStatus === Task.Status.Completed ||
                task.taskStatus === Task.Status.Dropped) {
                return false;
            }
        }

        // Filter by project_id
        if (filters.project_id !== undefined) {
            if (!task.containingProject || task.containingProject.id.primaryKey !== filters.project_id) {
                return false;
            }
        }

        // Filter by project_name (case-insensitive partial match)
        if (filters.project_name !== undefined) {
            var projectNameLower = filters.project_name.toLowerCase();
            if (task.containingProject) {
                var projectName = task.containingProject.name.toLowerCase();
                if (!projectName.includes(projectNameLower)) {
                    return false;
                }
            } else if (projectNameLower !== "inbox") {
                return false;
            }
        }

        // Filter by flagged
        if (filters.flagged !== undefined) {
            if (task.flagged !== filters.flagged) {
                return false;
            }
        }

        // Filter by tags (OR logic)
        if (filters.tags !== undefined && filters.tags.length > 0) {
            var itemTagNames = task.tags ? task.tags.map(function(t) { return t.name; }) : [];
            if (!filters.tags.some(function(ft) { return itemTagNames.includes(ft); })) {
                return false;
            }
        }

        // Filter by status
        if (filters.status !== undefined && filters.status.length > 0) {
            var itemStatus = taskStatusMap[task.taskStatus];
            var normalizedStatuses = filters.status.map(function(s) { return statusNameMap[s] || s; });
            if (!normalizedStatuses.includes(itemStatus)) {
                return false;
            }
        }

        // Filter by due_within N days
        if (filters.due_within !== undefined) {
            if (!isWithinDays(task.dueDate, filters.due_within, true)) {
                return false;
            }
        }

        // Filter by deferred_until N days
        if (filters.deferred_until !== undefined) {
            if (!isWithinDays(task.deferDate, filters.deferred_until, false)) {
                return false;
            }
        }

        // Filter by planned_within N days (OmniFocus 4.7+)
        if (filters.planned_within !== undefined) {
            if (!isWithinDays(task.plannedDate, filters.planned_within, true)) {
                return false;
            }
        }

        // Filter by has_note
        if (filters.has_note !== undefined) {
            var hasNote = task.note && task.note.trim() !== "";
            if (filters.has_note !== hasNote) {
                return false;
            }
        }

        return true;
    };
}

/**
 * Create a filter function for projects.
 * @param {Object} filters - Filter criteria
 * @param {Object} options - Additional options
 * @param {boolean} options.includeCompleted - Include completed/dropped projects
 * @returns {Function} Filter function for projects
 */
function createProjectFilter(filters, options) {
    var includeCompleted = options.includeCompleted || false;

    return function(project) {
        // Completed/dropped filter
        if (!includeCompleted) {
            if (project.status === Project.Status.Done ||
                project.status === Project.Status.Dropped) {
                return false;
            }
        }

        // Filter by folder_id
        if (filters.folder_id !== undefined) {
            if (!project.folder || project.folder.id.primaryKey !== filters.folder_id) {
                return false;
            }
        }

        // Filter by status (OR logic between statuses)
        if (filters.status !== undefined && filters.status.length > 0) {
            var projectStatus = projectStatusMap[project.status];
            var normalizedStatuses = filters.status.map(function(s) { return statusNameMap[s] || s; });
            if (!normalizedStatuses.includes(projectStatus)) {
                return false;
            }
        }

        // Filter by available (Active + not deferred)
        if (filters.available !== undefined && filters.available === true) {
            if (project.status !== Project.Status.Active) {
                return false;
            }
            if (project.deferDate && project.deferDate > new Date()) {
                return false;
            }
        }

        // Filter by flagged
        if (filters.flagged !== undefined) {
            if (project.flagged !== filters.flagged) {
                return false;
            }
        }

        // Filter by sequential
        if (filters.sequential !== undefined) {
            if (project.sequential !== filters.sequential) {
                return false;
            }
        }

        // Filter by tags (OR logic)
        if (filters.tags !== undefined && filters.tags.length > 0) {
            var projectTagNames = project.tags ? project.tags.map(function(t) { return t.name; }) : [];
            if (!filters.tags.some(function(ft) { return projectTagNames.includes(ft); })) {
                return false;
            }
        }

        // Filter by due_within N days
        if (filters.due_within !== undefined) {
            if (!isWithinDays(project.dueDate, filters.due_within, true)) {
                return false;
            }
        }

        // Filter by deferred_until N days
        if (filters.deferred_until !== undefined) {
            if (!isWithinDays(project.deferDate, filters.deferred_until, false)) {
                return false;
            }
        }

        // Filter by has_note
        if (filters.has_note !== undefined) {
            var hasNote = project.note && project.note.trim() !== "";
            if (filters.has_note !== hasNote) {
                return false;
            }
        }

        return true;
    };
}
