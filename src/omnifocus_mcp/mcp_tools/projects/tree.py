"""Get tree tool - hierarchical view of folders, projects, and tasks."""

import json
from typing import Any, Optional
from ...omnijs import execute_omnijs


def _build_project_filter_conditions(filters: dict) -> str:
    """Build JavaScript filter conditions for projects."""
    conditions = []

    # Filter by project status (OR logic between statuses)
    if filters.get("status"):
        status_list = filters["status"]
        status_checks = []
        for status in status_list:
            status_upper = status[0].upper() + status[1:] if status else ""
            # Map common names to OmniFocus status names
            status_map = {
                "Active": "Active",
                "Done": "Done",
                "Completed": "Done",
                "Dropped": "Dropped",
                "OnHold": "OnHold",
                "On Hold": "OnHold",
                "on_hold": "OnHold",
            }
            mapped_status = status_map.get(status, status_map.get(status_upper, status_upper))
            status_checks.append(f'projectStatusMap[project.status] === "{mapped_status}"')
        if status_checks:
            conditions.append(f'''
                if (!({" || ".join(status_checks)})) {{
                    return false;
                }}
            ''')

    # Filter by flagged
    if filters.get("flagged") is not None:
        flagged_val = "true" if filters["flagged"] else "false"
        conditions.append(f'''
            if (project.flagged !== {flagged_val}) {{
                return false;
            }}
        ''')

    # Filter by sequential
    if filters.get("sequential") is not None:
        sequential_val = "true" if filters["sequential"] else "false"
        conditions.append(f'''
            if (project.sequential !== {sequential_val}) {{
                return false;
            }}
        ''')

    # Filter by tags (OR logic)
    if filters.get("tags"):
        tags_json = json.dumps(filters["tags"])
        conditions.append(f'''
            const filterTags = {tags_json};
            const projectTagNames = project.tags ? project.tags.map(t => t.name) : [];
            if (!filterTags.some(ft => projectTagNames.includes(ft))) {{
                return false;
            }}
        ''')

    # Filter by due within N days
    if filters.get("due_within") is not None:
        conditions.append(f'''
            if (!project.dueDate) {{
                return false;
            }}
            const now = new Date();
            const futureDate = new Date();
            futureDate.setDate(futureDate.getDate() + {filters["due_within"]});
            if (project.dueDate > futureDate || project.dueDate < now) {{
                return false;
            }}
        ''')

    # Filter by deferred until N days
    if filters.get("deferred_until") is not None:
        conditions.append(f'''
            if (!project.deferDate) {{
                return false;
            }}
            const now = new Date();
            const futureDate = new Date();
            futureDate.setDate(futureDate.getDate() + {filters["deferred_until"]});
            if (project.deferDate > futureDate) {{
                return false;
            }}
        ''')

    # Filter by has note
    if filters.get("has_note") is not None:
        if filters["has_note"]:
            conditions.append('''
                if (!project.note || project.note.trim() === "") {
                    return false;
                }
            ''')
        else:
            conditions.append('''
                if (project.note && project.note.trim() !== "") {
                    return false;
                }
            ''')

    return "\n".join(conditions)


async def get_tree(
    parent_id: Optional[str] = None,
    parent_name: Optional[str] = None,
    filters: Optional[dict[str, Any]] = None,
    include_completed: bool = False,
    max_depth: Optional[int] = None,
    include_root_projects: bool = True,
    summary: bool = False,
    fields: Optional[list[str]] = None,
    include_folders: bool = True,
    include_projects: bool = True,
    include_tasks: bool = False,
) -> str:
    """
    Get a hierarchical tree of folders, projects, and tasks.

    Returns a tree structure showing the folder/project/task hierarchy in OmniFocus.
    Supports filtering by various criteria and starting from a specific folder.

    Args:
        parent_id: Start traversal from folder with this ID (optional)
        parent_name: Start traversal from folder with this name (optional, case-insensitive,
            supports partial matching - e.g. "Goals" matches "🎯 Goals")
        filters: Optional filters for projects (all AND logic):
            - status: Filter by project status (list, OR logic).
                      Values: 'Active', 'Done', 'Dropped', 'OnHold'
            - flagged: Filter by flagged status (boolean)
            - sequential: Filter by sequential setting (boolean)
            - tags: Filter by tag names (list, OR logic - project has ANY of the tags)
            - due_within: Projects due within N days from today
            - deferred_until: Projects deferred becoming available within N days
            - has_note: Filter by note presence (boolean)
        include_completed: Include completed/dropped projects and tasks (default: False)
        max_depth: Maximum folder depth to traverse (None = unlimited)
        include_root_projects: Include projects at root level (not in any folder) (default: True)
        summary: If True, return only counts (projectCount, folderCount, taskCount) without tree
        fields: Specific project/task fields to return (reduces response size).
            Project fields: id, name, status, sequential, flagged, dueDate, deferDate,
            estimatedMinutes, taskCount, tagNames.
            Task fields: id, name, flagged, dueDate, deferDate, estimatedMinutes, tagNames,
            completed, note.
            If not specified, returns all fields.
        include_folders: Include folder nodes in the tree (default: True)
        include_projects: Include project nodes in the tree (default: True)
        include_tasks: Include tasks within each project (default: False).
            When True, projects will have a "tasks" array with their tasks.

    Returns:
        JSON string with hierarchical tree structure (or just counts if summary=True):
        {
            "tree": [
                {
                    "type": "folder",
                    "id": "...",
                    "name": "Folder Name",
                    "children": [
                        {"type": "project", "id": "...", "name": "Project", "tasks": [...]},
                        {"type": "folder", "id": "...", "name": "Subfolder", "children": [...]}
                    ]
                },
                {"type": "project", "id": "...", "name": "Root Project", ...}
            ],
            "projectCount": 10,
            "folderCount": 5,
            "taskCount": 42
        }
    """
    filters = filters or {}
    fields = fields or []

    # Build project filter conditions
    filter_conditions = _build_project_filter_conditions(filters)

    # Build completed filter
    completed_filter = ""
    if not include_completed:
        completed_filter = '''
            if (project.status === Project.Status.Done ||
                project.status === Project.Status.Dropped) {
                return false;
            }
        '''

    # Handle parent_id and parent_name for starting point
    start_folder_logic = ""
    if parent_id:
        start_folder_logic = f'''
            const startFolder = flattenedFolders.find(f => f.id.primaryKey === "{parent_id}");
            if (!startFolder) {{
                return JSON.stringify({{
                    error: "Folder not found with ID: {parent_id}"
                }});
            }}
            rootFolders = [startFolder];
            includeRootProjects = false;
        '''
    elif parent_name:
        parent_name_lower = parent_name.lower().replace('"', '\\"')
        parent_name_escaped = parent_name.replace('"', '\\"')
        start_folder_logic = f'''
            // First try exact case-insensitive match
            let startFolder = flattenedFolders.find(f => f.name.toLowerCase() === "{parent_name_lower}");

            if (!startFolder) {{
                // Try partial match (folder name contains search term)
                const partialMatches = flattenedFolders.filter(f =>
                    f.name.toLowerCase().includes("{parent_name_lower}")
                );

                if (partialMatches.length === 1) {{
                    // Single partial match - use it
                    startFolder = partialMatches[0];
                }} else if (partialMatches.length > 1) {{
                    // Multiple partial matches - return suggestions
                    return JSON.stringify({{
                        error: "Folder not found with name: {parent_name_escaped}",
                        suggestions: partialMatches.map(f => ({{
                            id: f.id.primaryKey,
                            name: f.name
                        }}))
                    }});
                }} else {{
                    // No matches at all
                    return JSON.stringify({{
                        error: "Folder not found with name: {parent_name_escaped}"
                    }});
                }}
            }}
            rootFolders = [startFolder];
            includeRootProjects = false;
        '''

    # Max depth logic
    max_depth_val = "null" if max_depth is None else str(max_depth)
    include_root_projects_val = "true" if include_root_projects else "false"
    summary_val = "true" if summary else "false"
    fields_json = json.dumps(fields)
    include_folders_val = "true" if include_folders else "false"
    include_projects_val = "true" if include_projects else "false"
    include_tasks_val = "true" if include_tasks else "false"

    # Build task completed filter
    task_completed_filter = ""
    if not include_completed:
        task_completed_filter = '''
            if (task.completed) {
                return false;
            }
        '''

    script = f'''
    (() => {{
        try {{
            const projectStatusMap = {{}};
            projectStatusMap[Project.Status.Active] = "Active";
            projectStatusMap[Project.Status.Done] = "Done";
            projectStatusMap[Project.Status.Dropped] = "Dropped";
            projectStatusMap[Project.Status.OnHold] = "OnHold";

            const taskStatusMap = {{}};
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
            const maxDepth = {max_depth_val};
            let includeRootProjects = {include_root_projects_val};
            const summaryOnly = {summary_val};
            const requestedFields = {fields_json};
            const includeFolders = {include_folders_val};
            const includeProjects = {include_projects_val};
            const includeTasks = {include_tasks_val};

            // Function to check if a project passes the filters
            function projectPassesFilter(project) {{
                // Completed/dropped filter
                {completed_filter}

                // User filters
                {filter_conditions}

                return true;
            }}

            // Function to check if a task passes filters
            function taskPassesFilter(task) {{
                {task_completed_filter}
                return true;
            }}

            // Function to map a task to output format
            function mapTask(task) {{
                const allFields = {{
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
                }};

                // If no specific fields requested, return all
                if (requestedFields.length === 0) {{
                    return allFields;
                }}

                // Return only requested fields (always include type)
                const result = {{ type: "task" }};
                for (const field of requestedFields) {{
                    if (field in allFields) {{
                        result[field] = allFields[field];
                    }}
                }}
                return result;
            }}

            // Function to map a project to output format
            function mapProject(project) {{
                const allFields = {{
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
                }};

                // If no specific fields requested, return all
                if (requestedFields.length === 0) {{
                    // Add tasks if requested
                    if (includeTasks && project.tasks) {{
                        const tasks = [];
                        for (const task of project.tasks) {{
                            if (taskPassesFilter(task)) {{
                                taskCount++;
                                tasks.push(mapTask(task));
                            }}
                        }}
                        allFields.tasks = tasks;
                    }}
                    return allFields;
                }}

                // Return only requested fields (always include type)
                const result = {{ type: "project" }};
                for (const field of requestedFields) {{
                    if (field in allFields) {{
                        result[field] = allFields[field];
                    }}
                }}
                // Add tasks if requested (even with field filtering)
                if (includeTasks && project.tasks) {{
                    const tasks = [];
                    for (const task of project.tasks) {{
                        if (taskPassesFilter(task)) {{
                            taskCount++;
                            tasks.push(mapTask(task));
                        }}
                    }}
                    result.tasks = tasks;
                }}
                return result;
            }}

            // Count projects/tasks in a folder recursively (for summary mode)
            function countProjectsInFolder(folder, currentDepth) {{
                folderCount++;

                // Check depth limit
                if (maxDepth !== null && currentDepth >= maxDepth) {{
                    return;
                }}

                // Count in child folders
                if (folder.folders) {{
                    for (const childFolder of folder.folders) {{
                        countProjectsInFolder(childFolder, currentDepth + 1);
                    }}
                }}

                // Count projects in this folder
                if (folder.projects) {{
                    for (const project of folder.projects) {{
                        if (projectPassesFilter(project)) {{
                            projectCount++;
                            // Count tasks if requested
                            if (includeTasks && project.tasks) {{
                                for (const task of project.tasks) {{
                                    if (taskPassesFilter(task)) {{
                                        taskCount++;
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}

            // Function to build folder tree recursively
            function buildFolderTree(folder, currentDepth) {{
                folderCount++;
                const result = {{
                    type: "folder",
                    id: folder.id.primaryKey,
                    name: folder.name,
                    children: []
                }};

                // Check depth limit
                if (maxDepth !== null && currentDepth >= maxDepth) {{
                    return result;
                }}

                // Add child folders
                if (folder.folders && includeFolders) {{
                    for (const childFolder of folder.folders) {{
                        const childTree = buildFolderTree(childFolder, currentDepth + 1);
                        // Only include folder if it has children or matching projects
                        if (childTree.children.length > 0 || hasMatchingProjects(childFolder)) {{
                            result.children.push(childTree);
                        }}
                    }}
                }}

                // Add projects in this folder
                if (folder.projects && includeProjects) {{
                    for (const project of folder.projects) {{
                        if (projectPassesFilter(project)) {{
                            projectCount++;
                            result.children.push(mapProject(project));
                        }}
                    }}
                }}

                return result;
            }}

            // Check if a folder or its descendants have matching projects
            function hasMatchingProjects(folder) {{
                if (folder.projects) {{
                    for (const project of folder.projects) {{
                        if (projectPassesFilter(project)) {{
                            return true;
                        }}
                    }}
                }}
                if (folder.folders) {{
                    for (const childFolder of folder.folders) {{
                        if (hasMatchingProjects(childFolder)) {{
                            return true;
                        }}
                    }}
                }}
                return false;
            }}

            // Get root folders (folders without parent)
            // Note: Use .parent for folders (not .folder which is for projects)
            let rootFolders = flattenedFolders.filter(f => !f.parent);

            // Apply start folder logic if specified
            {start_folder_logic}

            // Summary mode: just count, don't build tree
            if (summaryOnly) {{
                for (const folder of rootFolders) {{
                    countProjectsInFolder(folder, 0);
                }}

                // Count root-level projects
                if (includeRootProjects) {{
                    const rootProjects = flattenedProjects.filter(p => !p.folder);
                    for (const project of rootProjects) {{
                        if (projectPassesFilter(project)) {{
                            projectCount++;
                            // Count tasks if requested
                            if (includeTasks && project.tasks) {{
                                for (const task of project.tasks) {{
                                    if (taskPassesFilter(task)) {{
                                        taskCount++;
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}

                const summaryResult = {{
                    projectCount: projectCount,
                    folderCount: folderCount
                }};
                if (includeTasks) {{
                    summaryResult.taskCount = taskCount;
                }}
                return JSON.stringify(summaryResult);
            }}

            const tree = [];

            // Add root-level folders
            if (includeFolders) {{
                for (const folder of rootFolders) {{
                    const folderTree = buildFolderTree(folder, 0);
                    // Include folder if it has children
                    if (folderTree.children.length > 0) {{
                        tree.push(folderTree);
                    }}
                }}
            }} else if (includeProjects) {{
                // No folders, but traverse to find all projects
                function collectProjects(folder) {{
                    if (folder.projects) {{
                        for (const project of folder.projects) {{
                            if (projectPassesFilter(project)) {{
                                projectCount++;
                                tree.push(mapProject(project));
                            }}
                        }}
                    }}
                    if (folder.folders) {{
                        for (const childFolder of folder.folders) {{
                            collectProjects(childFolder);
                        }}
                    }}
                }}
                for (const folder of rootFolders) {{
                    folderCount++;
                    collectProjects(folder);
                }}
            }}

            // Add root-level projects (projects not in any folder)
            if (includeRootProjects && includeProjects) {{
                const rootProjects = flattenedProjects.filter(p => !p.folder);
                for (const project of rootProjects) {{
                    if (projectPassesFilter(project)) {{
                        projectCount++;
                        tree.push(mapProject(project));
                    }}
                }}
            }}

            const finalResult = {{
                tree: tree,
                projectCount: projectCount,
                folderCount: folderCount
            }};
            if (includeTasks) {{
                finalResult.taskCount = taskCount;
            }}
            return JSON.stringify(finalResult);

        }} catch (error) {{
            return JSON.stringify({{
                error: "Failed to get project tree: " + error.toString()
            }});
        }}
    }})();
    '''

    try:
        result = await execute_omnijs(script)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
