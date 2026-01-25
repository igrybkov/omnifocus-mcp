// Get hierarchical tree of folders, projects, and tasks
// Params: {
//   parent_id: string | null,
//   parent_name: string | null,
//   filters: object,
//   include_completed: boolean,
//   max_depth: number | null,
//   include_root_projects: boolean,
//   summary: boolean,
//   fields: string[],
//   include_folders: boolean,
//   include_projects: boolean,
//   include_tasks: boolean
// }

try {
    const projectStatusMap = {};
    projectStatusMap[Project.Status.Active] = "Active";
    projectStatusMap[Project.Status.Done] = "Done";
    projectStatusMap[Project.Status.Dropped] = "Dropped";
    projectStatusMap[Project.Status.OnHold] = "OnHold";

    const taskStatusMap = {};
    taskStatusMap[Task.Status.Available] = "Available";
    taskStatusMap[Task.Status.Blocked] = "Blocked";
    taskStatusMap[Task.Status.Completed] = "Completed";
    taskStatusMap[Task.Status.Dropped] = "Dropped";
    taskStatusMap[Task.Status.DueSoon] = "DueSoon";
    taskStatusMap[Task.Status.Next] = "Next";
    taskStatusMap[Task.Status.Overdue] = "Overdue";

    let projectCount = 0;
    let folderCount = 0;
    let taskCount = 0;

    const filters = params.filters || {};
    const maxDepth = params.max_depth;
    let includeRootProjects = params.include_root_projects;
    const summaryOnly = params.summary;
    const requestedFields = params.fields || [];
    const includeFolders = params.include_folders;
    const includeProjects = params.include_projects;
    const includeTasks = params.include_tasks;
    const includeCompleted = params.include_completed;

    // Status mapping for filter comparisons
    const statusNameMap = {
        "active": "Active",
        "Active": "Active",
        "done": "Done",
        "Done": "Done",
        "completed": "Done",
        "Completed": "Done",
        "dropped": "Dropped",
        "Dropped": "Dropped",
        "onhold": "OnHold",
        "OnHold": "OnHold",
        "on_hold": "OnHold",
        "On Hold": "OnHold"
    };

    // Function to check if a project passes the filters
    function projectPassesFilter(project) {
        // Completed/dropped filter
        if (!includeCompleted) {
            if (project.status === Project.Status.Done ||
                project.status === Project.Status.Dropped) {
                return false;
            }
        }

        // Filter by project status (OR logic between statuses)
        if (filters.status && filters.status.length > 0) {
            const projectStatus = projectStatusMap[project.status];
            const normalizedStatuses = filters.status.map(s => statusNameMap[s] || s);
            if (!normalizedStatuses.includes(projectStatus)) {
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
        if (filters.tags && filters.tags.length > 0) {
            const projectTagNames = project.tags ? project.tags.map(t => t.name) : [];
            if (!filters.tags.some(ft => projectTagNames.includes(ft))) {
                return false;
            }
        }

        // Filter by due_within N days
        if (filters.due_within !== undefined) {
            if (!project.dueDate) {
                return false;
            }
            const now = new Date();
            const futureDate = new Date();
            futureDate.setDate(futureDate.getDate() + filters.due_within);
            if (project.dueDate > futureDate || project.dueDate < now) {
                return false;
            }
        }

        // Filter by deferred_until N days
        if (filters.deferred_until !== undefined) {
            if (!project.deferDate) {
                return false;
            }
            const now = new Date();
            const futureDate = new Date();
            futureDate.setDate(futureDate.getDate() + filters.deferred_until);
            if (project.deferDate > futureDate) {
                return false;
            }
        }

        // Filter by has_note
        if (filters.has_note !== undefined) {
            const hasNote = project.note && project.note.trim() !== "";
            if (filters.has_note !== hasNote) {
                return false;
            }
        }

        return true;
    }

    // Function to check if a task passes filters
    function taskPassesFilter(task) {
        if (!includeCompleted && task.completed) {
            return false;
        }
        return true;
    }

    // Function to map a task to output format
    function mapTask(task) {
        const allFields = {
            type: "task",
            id: task.id.primaryKey,
            name: task.name,
            status: taskStatusMap[task.taskStatus] || "Unknown",
            flagged: task.flagged || false,
            completed: task.completed || false,
            dueDate: task.dueDate ? task.dueDate.toISOString() : null,
            deferDate: task.deferDate ? task.deferDate.toISOString() : null,
            estimatedMinutes: task.estimatedMinutes || null,
            tagNames: task.tags ? task.tags.map(t => t.name) : [],
            note: task.note || ""
        };

        // If no specific fields requested, return all
        if (requestedFields.length === 0) {
            return allFields;
        }

        // Return only requested fields (always include type)
        const result = { type: "task" };
        for (const field of requestedFields) {
            if (field in allFields) {
                result[field] = allFields[field];
            }
        }
        return result;
    }

    // Function to map a project to output format
    function mapProject(project) {
        const allFields = {
            type: "project",
            id: project.id.primaryKey,
            name: project.name,
            status: projectStatusMap[project.status] || "Unknown",
            sequential: project.sequential || false,
            flagged: project.flagged || false,
            dueDate: project.dueDate ? project.dueDate.toISOString() : null,
            deferDate: project.deferDate ? project.deferDate.toISOString() : null,
            estimatedMinutes: project.estimatedMinutes || null,
            taskCount: project.flattenedTasks ? project.flattenedTasks.length : 0,
            tagNames: project.tags ? project.tags.map(t => t.name) : []
        };

        // If no specific fields requested, return all
        if (requestedFields.length === 0) {
            // Add tasks if requested
            if (includeTasks && project.tasks) {
                const tasks = [];
                for (const task of project.tasks) {
                    if (taskPassesFilter(task)) {
                        taskCount++;
                        tasks.push(mapTask(task));
                    }
                }
                allFields.tasks = tasks;
            }
            return allFields;
        }

        // Return only requested fields (always include type)
        const result = { type: "project" };
        for (const field of requestedFields) {
            if (field in allFields) {
                result[field] = allFields[field];
            }
        }
        // Add tasks if requested (even with field filtering)
        if (includeTasks && project.tasks) {
            const tasks = [];
            for (const task of project.tasks) {
                if (taskPassesFilter(task)) {
                    taskCount++;
                    tasks.push(mapTask(task));
                }
            }
            result.tasks = tasks;
        }
        return result;
    }

    // Count projects/tasks in a folder recursively (for summary mode)
    function countProjectsInFolder(folder, currentDepth) {
        folderCount++;

        // Check depth limit
        if (maxDepth !== null && currentDepth >= maxDepth) {
            return;
        }

        // Count in child folders
        if (folder.folders) {
            for (const childFolder of folder.folders) {
                countProjectsInFolder(childFolder, currentDepth + 1);
            }
        }

        // Count projects in this folder
        if (folder.projects) {
            for (const project of folder.projects) {
                if (projectPassesFilter(project)) {
                    projectCount++;
                    // Count tasks if requested
                    if (includeTasks && project.tasks) {
                        for (const task of project.tasks) {
                            if (taskPassesFilter(task)) {
                                taskCount++;
                            }
                        }
                    }
                }
            }
        }
    }

    // Check if a folder or its descendants have matching projects
    function hasMatchingProjects(folder) {
        if (folder.projects) {
            for (const project of folder.projects) {
                if (projectPassesFilter(project)) {
                    return true;
                }
            }
        }
        if (folder.folders) {
            for (const childFolder of folder.folders) {
                if (hasMatchingProjects(childFolder)) {
                    return true;
                }
            }
        }
        return false;
    }

    // Function to build folder tree recursively
    function buildFolderTree(folder, currentDepth) {
        folderCount++;
        const result = {
            type: "folder",
            id: folder.id.primaryKey,
            name: folder.name,
            children: []
        };

        // Check depth limit
        if (maxDepth !== null && currentDepth >= maxDepth) {
            return result;
        }

        // Add child folders
        if (folder.folders && includeFolders) {
            for (const childFolder of folder.folders) {
                const childTree = buildFolderTree(childFolder, currentDepth + 1);
                // Only include folder if it has children or matching projects
                if (childTree.children.length > 0 || hasMatchingProjects(childFolder)) {
                    result.children.push(childTree);
                }
            }
        }

        // Add projects in this folder
        if (folder.projects && includeProjects) {
            for (const project of folder.projects) {
                if (projectPassesFilter(project)) {
                    projectCount++;
                    result.children.push(mapProject(project));
                }
            }
        }

        return result;
    }

    // Get root folders (folders without parent)
    let rootFolders = flattenedFolders.filter(f => !f.parent);

    // Apply start folder logic if specified
    if (params.parent_id) {
        const startFolder = flattenedFolders.find(f => f.id.primaryKey === params.parent_id);
        if (!startFolder) {
            return JSON.stringify({
                error: "Folder not found with ID: " + params.parent_id
            });
        }
        rootFolders = [startFolder];
        includeRootProjects = false;
    } else if (params.parent_name) {
        const parentNameLower = params.parent_name.toLowerCase();

        // First try exact case-insensitive match
        let startFolder = flattenedFolders.find(f => f.name.toLowerCase() === parentNameLower);

        if (!startFolder) {
            // Try partial match (folder name contains search term)
            const partialMatches = flattenedFolders.filter(f =>
                f.name.toLowerCase().includes(parentNameLower)
            );

            if (partialMatches.length === 1) {
                // Single partial match - use it
                startFolder = partialMatches[0];
            } else if (partialMatches.length > 1) {
                // Multiple partial matches - return suggestions
                return JSON.stringify({
                    error: "Folder not found with name: " + params.parent_name,
                    suggestions: partialMatches.map(f => ({
                        id: f.id.primaryKey,
                        name: f.name
                    }))
                });
            } else {
                // No matches at all
                return JSON.stringify({
                    error: "Folder not found with name: " + params.parent_name
                });
            }
        }
        rootFolders = [startFolder];
        includeRootProjects = false;
    }

    // Summary mode: just count, don't build tree
    if (summaryOnly) {
        for (const folder of rootFolders) {
            countProjectsInFolder(folder, 0);
        }

        // Count root-level projects
        if (includeRootProjects) {
            const rootProjects = flattenedProjects.filter(p => !p.folder);
            for (const project of rootProjects) {
                if (projectPassesFilter(project)) {
                    projectCount++;
                    // Count tasks if requested
                    if (includeTasks && project.tasks) {
                        for (const task of project.tasks) {
                            if (taskPassesFilter(task)) {
                                taskCount++;
                            }
                        }
                    }
                }
            }
        }

        const summaryResult = {
            projectCount: projectCount,
            folderCount: folderCount
        };
        if (includeTasks) {
            summaryResult.taskCount = taskCount;
        }
        return JSON.stringify(summaryResult);
    }

    const tree = [];

    // Add root-level folders
    if (includeFolders) {
        for (const folder of rootFolders) {
            const folderTree = buildFolderTree(folder, 0);
            // Include folder if it has children
            if (folderTree.children.length > 0) {
                tree.push(folderTree);
            }
        }
    } else if (includeProjects) {
        // No folders, but traverse to find all projects
        function collectProjects(folder) {
            if (folder.projects) {
                for (const project of folder.projects) {
                    if (projectPassesFilter(project)) {
                        projectCount++;
                        tree.push(mapProject(project));
                    }
                }
            }
            if (folder.folders) {
                for (const childFolder of folder.folders) {
                    collectProjects(childFolder);
                }
            }
        }
        for (const folder of rootFolders) {
            folderCount++;
            collectProjects(folder);
        }
    }

    // Add root-level projects (projects not in any folder)
    if (includeRootProjects && includeProjects) {
        const rootProjects = flattenedProjects.filter(p => !p.folder);
        for (const project of rootProjects) {
            if (projectPassesFilter(project)) {
                projectCount++;
                tree.push(mapProject(project));
            }
        }
    }

    const finalResult = {
        tree: tree,
        projectCount: projectCount,
        folderCount: folderCount
    };
    if (includeTasks) {
        finalResult.taskCount = taskCount;
    }
    return JSON.stringify(finalResult);

} catch (error) {
    return JSON.stringify({
        error: "Failed to get project tree: " + error.toString()
    });
}
