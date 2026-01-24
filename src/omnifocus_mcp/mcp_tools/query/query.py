"""Query OmniFocus database tool."""

import json
from typing import Any, Optional
from ...omnijs import execute_omnijs


def _build_filter_conditions(entity: str, filters: dict) -> str:
    """Build JavaScript filter conditions for the query."""
    conditions = []

    # Filter by project (for tasks)
    if filters.get("project_id"):
        conditions.append(f'''
            if (!item.containingProject || item.containingProject.id.primaryKey !== "{filters["project_id"]}") {{
                return false;
            }}
        ''')

    if filters.get("project_name"):
        project_name_lower = filters["project_name"].lower()
        conditions.append(f'''
            if (item.containingProject) {{
                const projectName = item.containingProject.name.toLowerCase();
                if (!projectName.includes("{project_name_lower}")) {{
                    return false;
                }}
            }} else if ("{project_name_lower}" !== "inbox") {{
                return false;
            }}
        ''')

    # Filter by folder (for projects)
    if filters.get("folder_id"):
        conditions.append(f'''
            if (!item.folder || item.folder.id.primaryKey !== "{filters["folder_id"]}") {{
                return false;
            }}
        ''')

    # Filter by tags (OR logic)
    if filters.get("tags"):
        tags_json = json.dumps(filters["tags"])
        conditions.append(f'''
            const filterTags = {tags_json};
            const itemTagNames = item.tags ? item.tags.map(t => t.name) : [];
            if (!filterTags.some(ft => itemTagNames.includes(ft))) {{
                return false;
            }}
        ''')

    # Filter by status
    if filters.get("status"):
        status_json = json.dumps(filters["status"])
        conditions.append(f'''
            const filterStatuses = {status_json};
            if (!filterStatuses.includes(taskStatusMap[item.taskStatus])) {{
                return false;
            }}
        ''')

    # Filter by flagged
    if filters.get("flagged") is not None:
        flagged_val = "true" if filters["flagged"] else "false"
        conditions.append(f'''
            if (item.flagged !== {flagged_val}) {{
                return false;
            }}
        ''')

    # Filter by due within N days
    if filters.get("due_within") is not None:
        conditions.append(f'''
            if (!item.dueDate) {{
                return false;
            }}
            const now = new Date();
            const futureDate = new Date();
            futureDate.setDate(futureDate.getDate() + {filters["due_within"]});
            if (item.dueDate > futureDate || item.dueDate < now) {{
                return false;
            }}
        ''')

    # Filter by deferred until N days
    if filters.get("deferred_until") is not None:
        conditions.append(f'''
            if (!item.deferDate) {{
                return false;
            }}
            const now = new Date();
            const futureDate = new Date();
            futureDate.setDate(futureDate.getDate() + {filters["deferred_until"]});
            if (item.deferDate > futureDate) {{
                return false;
            }}
        ''')

    # Filter by planned within N days (OmniFocus 4.7+)
    if filters.get("planned_within") is not None:
        conditions.append(f'''
            if (!item.plannedDate) {{
                return false;
            }}
            const plannedNow = new Date();
            const plannedFutureDate = new Date();
            plannedFutureDate.setDate(plannedFutureDate.getDate() + {filters["planned_within"]});
            if (item.plannedDate > plannedFutureDate || item.plannedDate < plannedNow) {{
                return false;
            }}
        ''')

    # Filter by has note
    if filters.get("has_note") is not None:
        if filters["has_note"]:
            conditions.append('''
                if (!item.note || item.note.trim() === "") {
                    return false;
                }
            ''')
        else:
            conditions.append('''
                if (item.note && item.note.trim() !== "") {
                    return false;
                }
            ''')

    return "\n".join(conditions)


def _build_field_mapper(entity: str, fields: Optional[list[str]]) -> str:
    """Build JavaScript code to map item to output fields."""
    if entity == "tasks":
        default_fields = ["id", "name", "taskStatus", "flagged", "dueDate", "deferDate", "projectName", "tagNames"]
    elif entity == "projects":
        default_fields = ["id", "name", "status", "sequential", "dueDate", "deferDate", "folderName", "taskCount"]
    else:  # folders
        default_fields = ["id", "name", "projectCount"]

    fields_to_use = fields if fields else default_fields

    return f'''
        const fieldsToInclude = {json.dumps(fields_to_use)};

        function mapItem(item) {{
            const result = {{}};

            for (const field of fieldsToInclude) {{
                switch (field) {{
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
                }}
            }}

            return result;
        }}
    '''


async def query_omnifocus(
    entity: str,
    filters: Optional[dict[str, Any]] = None,
    fields: Optional[list[str]] = None,
    limit: Optional[int] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    include_completed: bool = False,
    summary: bool = False,
) -> str:
    """
    Query OmniFocus database with powerful filters.

    Much faster than dump_database for targeted queries.

    Args:
        entity: Type to query: 'tasks', 'projects', or 'folders'
        filters: Optional filters (all AND logic):
            - project_id: Filter tasks by exact project ID
            - project_name: Filter tasks by project name (case-insensitive partial match)
            - folder_id: Filter projects by exact folder ID
            - tags: Filter by tag names (exact match, OR logic between tags)
            - status: Filter by status (OR logic)
            - flagged: Filter by flagged status
            - due_within: Items due within N days from today
            - deferred_until: Items deferred becoming available within N days
            - planned_within: Tasks planned within N days from today (OmniFocus 4.7+)
            - has_note: Filter by note presence
        fields: Specific fields to return (reduces response size). Task fields include:
            plannedDate, effectivePlannedDate, effectiveDueDate, effectiveDeferDate
        limit: Maximum number of items to return
        sort_by: Field to sort by (name, dueDate, deferDate, plannedDate, modificationDate, etc.)
        sort_order: Sort order: 'asc' or 'desc' (default: 'asc')
        include_completed: Include completed/dropped items (default: False)
        summary: Return only count of matches (default: False)

    Returns:
        JSON string with query results or count
    """
    filters = filters or {}

    # Build filter conditions
    filter_conditions = _build_filter_conditions(entity, filters)

    # Build field mapper
    field_mapper = _build_field_mapper(entity, fields)

    # Build sort logic
    sort_logic = ""
    if sort_by:
        sort_direction = -1 if sort_order == "desc" else 1
        sort_logic = f'''
            filtered.sort((a, b) => {{
                let aVal = a.{sort_by};
                let bVal = b.{sort_by};

                // Handle dates
                if (aVal instanceof Date) aVal = aVal.getTime();
                if (bVal instanceof Date) bVal = bVal.getTime();

                // Handle nulls
                if (aVal === null || aVal === undefined) return 1;
                if (bVal === null || bVal === undefined) return -1;

                // Compare
                if (aVal < bVal) return {-sort_direction};
                if (aVal > bVal) return {sort_direction};
                return 0;
            }});
        '''

    # Build limit logic
    limit_logic = ""
    if limit:
        limit_logic = f"filtered = filtered.slice(0, {limit});"

    # Determine include_completed filter
    completed_filter = ""
    if not include_completed:
        if entity == "tasks":
            completed_filter = '''
                if (item.taskStatus === Task.Status.Completed ||
                    item.taskStatus === Task.Status.Dropped) {
                    return false;
                }
            '''
        elif entity == "projects":
            completed_filter = '''
                if (item.status === Project.Status.Done ||
                    item.status === Project.Status.Dropped) {
                    return false;
                }
            '''

    # Build the OmniJS script
    script = f'''
    (() => {{
        try {{
            // Status mappings
            const taskStatusMap = {{}};
            taskStatusMap[Task.Status.Available] = "Available";
            taskStatusMap[Task.Status.Blocked] = "Blocked";
            taskStatusMap[Task.Status.Completed] = "Completed";
            taskStatusMap[Task.Status.Dropped] = "Dropped";
            taskStatusMap[Task.Status.DueSoon] = "DueSoon";
            taskStatusMap[Task.Status.Next] = "Next";
            taskStatusMap[Task.Status.Overdue] = "Overdue";

            const projectStatusMap = {{}};
            projectStatusMap[Project.Status.Active] = "Active";
            projectStatusMap[Project.Status.Done] = "Done";
            projectStatusMap[Project.Status.Dropped] = "Dropped";
            projectStatusMap[Project.Status.OnHold] = "OnHold";

            // Get items based on entity type
            let items = [];
            const entityType = "{entity}";

            if (entityType === "tasks") {{
                items = flattenedTasks;
            }} else if (entityType === "projects") {{
                items = flattenedProjects;
            }} else if (entityType === "folders") {{
                items = flattenedFolders;
            }}

            // Filter items
            let filtered = items.filter(item => {{
                // Completed/dropped filter
                {completed_filter}

                // User filters
                {filter_conditions}

                return true;
            }});

            // Sort if requested
            {sort_logic}

            // Limit if requested
            {limit_logic}

            // Return summary if requested
            if ({str(summary).lower()}) {{
                return JSON.stringify({{
                    count: filtered.length,
                    entity: entityType
                }});
            }}

            // Map to output format
            {field_mapper}

            const results = filtered.map(mapItem);

            return JSON.stringify({{
                count: results.length,
                entity: entityType,
                items: results
            }});

        }} catch (error) {{
            return JSON.stringify({{
                error: "Query error: " + error.toString()
            }});
        }}
    }})();
    '''

    try:
        result = await execute_omnijs(script)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
