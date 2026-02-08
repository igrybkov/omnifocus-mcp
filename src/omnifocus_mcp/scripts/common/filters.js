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

    if (days >= 0) {
        // Positive: due in the next N days
        var futureDate = new Date();
        futureDate.setDate(futureDate.getDate() + days);
        if (date > futureDate) {
            return false;
        }
        if (requirePastOrPresent && date < now) {
            return false;
        }
    } else {
        // Negative: overdue by up to N days
        var pastDate = new Date();
        pastDate.setDate(pastDate.getDate() + days);  // days is negative
        // Date must be in the past (< now) and not too far back (>= pastDate)
        if (date >= now) {
            return false;
        }
        if (date < pastDate) {
            return false;
        }
    }

    return true;
}

/**
 * Check if a date falls on a specific day (N days from today).
 * @param {Date|null} date - The date to check
 * @param {number} daysFromToday - Number of days from today (0=today, 1=tomorrow, -1=yesterday)
 * @returns {boolean} True if date falls on that specific day
 */
function isOnDay(date, daysFromToday) {
    if (!date) {
        return false;
    }
    var targetDate = new Date();
    targetDate.setDate(targetDate.getDate() + daysFromToday);

    // Get start of target day (midnight)
    var startOfDay = new Date(targetDate.getFullYear(), targetDate.getMonth(), targetDate.getDate());
    // Get end of target day (midnight next day)
    var endOfDay = new Date(startOfDay);
    endOfDay.setDate(endOfDay.getDate() + 1);

    return date >= startOfDay && date < endOfDay;
}

/**
 * Ensure a value is an array. Wraps strings/scalars in an array.
 * Returns undefined for null/undefined so filter guards can skip them.
 * @param {*} value - The value to coerce
 * @returns {Array|undefined} The value as an array, or undefined
 */
function ensureArray(value) {
    if (value === undefined || value === null) return undefined;
    if (Array.isArray(value)) return value;
    return [value];
}

/**
 * Validate filter keys against allowed sets.
 * @param {Object} filters - Filter object to validate
 * @param {Array<string>} allowedKeys - List of valid filter keys
 * @param {string} entityType - Type being filtered ('tasks', 'projects', 'folders')
 * @throws {Error} If unknown filter keys are found
 */
function validateFilters(filters, allowedKeys, entityType) {
    var filterKeys = Object.keys(filters);
    var unknownKeys = [];

    for (var i = 0; i < filterKeys.length; i++) {
        if (allowedKeys.indexOf(filterKeys[i]) === -1) {
            unknownKeys.push(filterKeys[i]);
        }
    }

    if (unknownKeys.length > 0) {
        throw new Error(
            "Unknown filter key(s) for " + entityType + ": " + unknownKeys.join(", ") + ". " +
            "Valid keys: " + allowedKeys.join(", ")
        );
    }
}

// Valid filter keys for each entity type
var TASK_FILTER_KEYS = [
    "item_ids", "project_id", "project_name", "flagged", "tags", "status",
    "due_within", "due_after", "due_before",
    "deferred_until", "deferred_on", "planned_within",
    "has_note", "completed_within", "completed_after", "completed_before",
    "modified_before"
];

var PROJECT_FILTER_KEYS = [
    "item_ids", "folder_id", "status", "available", "flagged", "sequential", "tags",
    "due_within", "due_after", "due_before",
    "deferred_until", "deferred_on",
    "has_note", "modified_before", "was_deferred", "stalled"
];

/**
 * Create a filter function for tasks.
 * @param {Object} filters - Filter criteria
 * @param {Object} options - Additional options
 * @param {boolean} options.includeCompleted - Include completed/dropped tasks
 * @returns {Function} Filter function for tasks
 */
function createTaskFilter(filters, options) {
    var includeCompleted = options.includeCompleted || false;

    // Validate filter keys
    validateFilters(filters, TASK_FILTER_KEYS, "tasks");

    // Normalize array-type filters (callers may pass strings instead of arrays)
    filters.status = ensureArray(filters.status);
    filters.tags = ensureArray(filters.tags);
    filters.item_ids = ensureArray(filters.item_ids);

    return function(task) {
        // Completed/dropped filter
        if (!includeCompleted) {
            if (task.taskStatus === Task.Status.Completed ||
                task.taskStatus === Task.Status.Dropped) {
                return false;
            }
        }

        // Filter by item_ids (OR logic - task ID matches any in the list)
        if (filters.item_ids !== undefined && filters.item_ids.length > 0) {
            if (filters.item_ids.indexOf(task.id.primaryKey) === -1) {
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

        // Filter by due_after (tasks due on or after this date)
        // Value is days from today (negative for past dates)
        if (filters.due_after !== undefined) {
            if (!task.dueDate) {
                return false;
            }
            var afterDate = new Date();
            afterDate.setDate(afterDate.getDate() + filters.due_after);
            // Start of that day
            afterDate = new Date(afterDate.getFullYear(), afterDate.getMonth(), afterDate.getDate());
            if (task.dueDate < afterDate) {
                return false;
            }
        }

        // Filter by due_before (tasks due before the end of this date)
        // Value is days from today (negative for past dates)
        if (filters.due_before !== undefined) {
            if (!task.dueDate) {
                return false;
            }
            var beforeDate = new Date();
            beforeDate.setDate(beforeDate.getDate() + filters.due_before);
            // End of that day (midnight next day)
            beforeDate = new Date(beforeDate.getFullYear(), beforeDate.getMonth(), beforeDate.getDate() + 1);
            if (task.dueDate >= beforeDate) {
                return false;
            }
        }

        // Filter by deferred_until N days
        if (filters.deferred_until !== undefined) {
            if (!isWithinDays(task.deferDate, filters.deferred_until, false)) {
                return false;
            }
        }

        // Filter by deferred_on (exact date match)
        if (filters.deferred_on !== undefined) {
            if (!isOnDay(task.deferDate, filters.deferred_on)) {
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

        // Filter by completed_within N days (tasks completed in last N days)
        if (filters.completed_within !== undefined) {
            if (!task.completionDate) {
                return false;
            }
            var cutoff = new Date();
            cutoff.setDate(cutoff.getDate() - filters.completed_within);
            if (task.completionDate < cutoff) {
                return false;
            }
        }

        // Filter by completed_after (tasks completed on or after this date)
        // Value is days from today (negative for past dates)
        if (filters.completed_after !== undefined) {
            if (!task.completionDate) {
                return false;
            }
            var afterDate = new Date();
            afterDate.setDate(afterDate.getDate() + filters.completed_after);
            // Start of that day
            afterDate = new Date(afterDate.getFullYear(), afterDate.getMonth(), afterDate.getDate());
            if (task.completionDate < afterDate) {
                return false;
            }
        }

        // Filter by completed_before (tasks completed before the end of this date)
        // Value is days from today (negative for past dates)
        if (filters.completed_before !== undefined) {
            if (!task.completionDate) {
                return false;
            }
            var beforeDate = new Date();
            beforeDate.setDate(beforeDate.getDate() + filters.completed_before);
            // End of that day (midnight next day)
            beforeDate = new Date(beforeDate.getFullYear(), beforeDate.getMonth(), beforeDate.getDate() + 1);
            if (task.completionDate >= beforeDate) {
                return false;
            }
        }

        // Filter by modified_before N days (tasks NOT modified in last N days)
        if (filters.modified_before !== undefined) {
            var modCutoff = new Date();
            modCutoff.setDate(modCutoff.getDate() - filters.modified_before);
            // If no modification date or modified after cutoff, exclude
            if (!task.modificationDate || task.modificationDate > modCutoff) {
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

    // Validate filter keys
    validateFilters(filters, PROJECT_FILTER_KEYS, "projects");

    // Normalize array-type filters (callers may pass strings instead of arrays)
    filters.status = ensureArray(filters.status);
    filters.tags = ensureArray(filters.tags);
    filters.item_ids = ensureArray(filters.item_ids);

    return function(project) {
        // Completed/dropped filter
        if (!includeCompleted) {
            if (project.status === Project.Status.Done ||
                project.status === Project.Status.Dropped) {
                return false;
            }
        }

        // Filter by item_ids (OR logic - project ID matches any in the list)
        if (filters.item_ids !== undefined && filters.item_ids.length > 0) {
            if (filters.item_ids.indexOf(project.id.primaryKey) === -1) {
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

        // Filter by due_after (projects due on or after this date)
        // Value is days from today (negative for past dates)
        if (filters.due_after !== undefined) {
            if (!project.dueDate) {
                return false;
            }
            var afterDate = new Date();
            afterDate.setDate(afterDate.getDate() + filters.due_after);
            // Start of that day
            afterDate = new Date(afterDate.getFullYear(), afterDate.getMonth(), afterDate.getDate());
            if (project.dueDate < afterDate) {
                return false;
            }
        }

        // Filter by due_before (projects due before the end of this date)
        // Value is days from today (negative for past dates)
        if (filters.due_before !== undefined) {
            if (!project.dueDate) {
                return false;
            }
            var beforeDate = new Date();
            beforeDate.setDate(beforeDate.getDate() + filters.due_before);
            // End of that day (midnight next day)
            beforeDate = new Date(beforeDate.getFullYear(), beforeDate.getMonth(), beforeDate.getDate() + 1);
            if (project.dueDate >= beforeDate) {
                return false;
            }
        }

        // Filter by deferred_until N days
        if (filters.deferred_until !== undefined) {
            if (!isWithinDays(project.deferDate, filters.deferred_until, false)) {
                return false;
            }
        }

        // Filter by deferred_on (exact date match)
        if (filters.deferred_on !== undefined) {
            if (!isOnDay(project.deferDate, filters.deferred_on)) {
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

        // Filter by modified_before N days (projects NOT modified in last N days)
        if (filters.modified_before !== undefined) {
            var modCutoff = new Date();
            modCutoff.setDate(modCutoff.getDate() - filters.modified_before);
            // If no modification date or modified after cutoff, exclude
            if (!project.modificationDate || project.modificationDate > modCutoff) {
                return false;
            }
        }

        // Filter by was_deferred (projects with defer date in the past, now available)
        if (filters.was_deferred === true) {
            // Must have a defer date
            if (!project.deferDate) {
                return false;
            }
            // Defer date must be in the past (project has become available)
            if (project.deferDate >= new Date()) {
                return false;
            }
            // Must be active status
            if (project.status !== Project.Status.Active) {
                return false;
            }
        }

        // Filter by stalled (Active projects with no available tasks)
        if (filters.stalled === true) {
            // Must be active status
            if (project.status !== Project.Status.Active) {
                return false;
            }
            // Must not be deferred (defer date must be null or in the past)
            if (project.deferDate && project.deferDate > new Date()) {
                return false;
            }
            // Check for available tasks - if any task is Available or DueSoon, not stalled
            var hasAvailableTask = project.tasks.some(function(task) {
                return task.taskStatus === Task.Status.Available ||
                       task.taskStatus === Task.Status.DueSoon;
            });
            if (hasAvailableTask) {
                return false;
            }
        }

        return true;
    };
}
