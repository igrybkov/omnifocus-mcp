// Browse hierarchical tree of folders, projects, and tasks
// Requires: common/status_maps.js, common/filters.js, common/field_mappers.js
// Params: {
//   parent_id: string | null,
//   parent_name: string | null,
//   filters: object,
//   task_filters: object,
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
    var projectCount = 0;
    var folderCount = 0;
    var taskCount = 0;

    var filters = params.filters || {};
    var taskFilters = params.task_filters || {};
    var maxDepth = params.max_depth;
    var includeRootProjects = params.include_root_projects;
    var summaryOnly = params.summary;
    var requestedFields = params.fields || [];
    var includeFolders = params.include_folders;
    var includeProjects = params.include_projects;
    var includeTasks = params.include_tasks;
    var includeCompleted = params.include_completed;

    // Create filter functions using shared filters
    var projectPassesFilter = createProjectFilter(filters, { includeCompleted: includeCompleted });
    var taskPassesFilter = createTaskFilter(taskFilters, { includeCompleted: includeCompleted });

    // Function to map a task to output format
    function mapTask(task) {
        var result = mapTaskFields(task, requestedFields);
        result.type = "task";
        return result;
    }

    // Function to map a project to output format
    function mapProject(project) {
        var result = mapProjectFields(project, requestedFields);
        result.type = "project";

        // Add tasks if requested
        if (includeTasks && project.tasks) {
            var tasks = [];
            for (var i = 0; i < project.tasks.length; i++) {
                var task = project.tasks[i];
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
            for (var i = 0; i < folder.folders.length; i++) {
                countProjectsInFolder(folder.folders[i], currentDepth + 1);
            }
        }

        // Count projects in this folder
        if (folder.projects) {
            for (var j = 0; j < folder.projects.length; j++) {
                var project = folder.projects[j];
                if (projectPassesFilter(project)) {
                    projectCount++;
                    // Count tasks if requested
                    if (includeTasks && project.tasks) {
                        for (var k = 0; k < project.tasks.length; k++) {
                            if (taskPassesFilter(project.tasks[k])) {
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
            for (var i = 0; i < folder.projects.length; i++) {
                if (projectPassesFilter(folder.projects[i])) {
                    return true;
                }
            }
        }
        if (folder.folders) {
            for (var j = 0; j < folder.folders.length; j++) {
                if (hasMatchingProjects(folder.folders[j])) {
                    return true;
                }
            }
        }
        return false;
    }

    // Function to build folder tree recursively
    function buildFolderTree(folder, currentDepth) {
        folderCount++;
        var result = {
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
            for (var i = 0; i < folder.folders.length; i++) {
                var childFolder = folder.folders[i];
                var childTree = buildFolderTree(childFolder, currentDepth + 1);
                // Only include folder if it has children or matching projects
                if (childTree.children.length > 0 || hasMatchingProjects(childFolder)) {
                    result.children.push(childTree);
                }
            }
        }

        // Add projects in this folder
        if (folder.projects && includeProjects) {
            for (var j = 0; j < folder.projects.length; j++) {
                var project = folder.projects[j];
                if (projectPassesFilter(project)) {
                    projectCount++;
                    result.children.push(mapProject(project));
                }
            }
        }

        return result;
    }

    // Get root folders (folders without parent)
    var rootFolders = flattenedFolders.filter(function(f) { return !f.parent; });

    // Apply start folder logic if specified
    if (params.parent_id) {
        var startFolder = flattenedFolders.find(function(f) {
            return f.id.primaryKey === params.parent_id;
        });
        if (!startFolder) {
            return JSON.stringify({
                error: "Folder not found with ID: " + params.parent_id
            });
        }
        rootFolders = [startFolder];
        includeRootProjects = false;
    } else if (params.parent_name) {
        var parentNameLower = params.parent_name.toLowerCase();

        // First try exact case-insensitive match
        var startFolder = flattenedFolders.find(function(f) {
            return f.name.toLowerCase() === parentNameLower;
        });

        if (!startFolder) {
            // Try partial match (folder name contains search term)
            var partialMatches = flattenedFolders.filter(function(f) {
                return f.name.toLowerCase().includes(parentNameLower);
            });

            if (partialMatches.length === 1) {
                // Single partial match - use it
                startFolder = partialMatches[0];
            } else if (partialMatches.length > 1) {
                // Multiple partial matches - return suggestions
                return JSON.stringify({
                    error: "Folder not found with name: " + params.parent_name,
                    suggestions: partialMatches.map(function(f) {
                        return { id: f.id.primaryKey, name: f.name };
                    })
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
        for (var i = 0; i < rootFolders.length; i++) {
            countProjectsInFolder(rootFolders[i], 0);
        }

        // Count root-level projects
        if (includeRootProjects) {
            var rootProjects = flattenedProjects.filter(function(p) { return !p.folder; });
            for (var j = 0; j < rootProjects.length; j++) {
                var project = rootProjects[j];
                if (projectPassesFilter(project)) {
                    projectCount++;
                    // Count tasks if requested
                    if (includeTasks && project.tasks) {
                        for (var k = 0; k < project.tasks.length; k++) {
                            if (taskPassesFilter(project.tasks[k])) {
                                taskCount++;
                            }
                        }
                    }
                }
            }
        }

        var summaryResult = {
            projectCount: projectCount,
            folderCount: folderCount
        };
        if (includeTasks) {
            summaryResult.taskCount = taskCount;
        }
        return JSON.stringify(summaryResult);
    }

    var tree = [];

    // Add root-level folders
    if (includeFolders) {
        for (var i = 0; i < rootFolders.length; i++) {
            var folderTree = buildFolderTree(rootFolders[i], 0);
            // Include folder if it has children
            if (folderTree.children.length > 0) {
                tree.push(folderTree);
            }
        }
    } else if (includeProjects) {
        // No folders, but traverse to find all projects
        function collectProjects(folder) {
            if (folder.projects) {
                for (var i = 0; i < folder.projects.length; i++) {
                    var project = folder.projects[i];
                    if (projectPassesFilter(project)) {
                        projectCount++;
                        tree.push(mapProject(project));
                    }
                }
            }
            if (folder.folders) {
                for (var j = 0; j < folder.folders.length; j++) {
                    collectProjects(folder.folders[j]);
                }
            }
        }
        for (var i = 0; i < rootFolders.length; i++) {
            folderCount++;
            collectProjects(rootFolders[i]);
        }
    }

    // Add root-level projects (projects not in any folder)
    if (includeRootProjects && includeProjects) {
        var rootProjects = flattenedProjects.filter(function(p) { return !p.folder; });
        for (var i = 0; i < rootProjects.length; i++) {
            var project = rootProjects[i];
            if (projectPassesFilter(project)) {
                projectCount++;
                tree.push(mapProject(project));
            }
        }
    }

    var finalResult = {
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
        error: "Failed to browse project tree: " + error.toString()
    });
}
