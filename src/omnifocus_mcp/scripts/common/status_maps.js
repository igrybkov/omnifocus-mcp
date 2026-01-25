// Status mappings for OmniFocus entities
// Shared between search.js and browse.js

// Task status enum to string mapping
var taskStatusMap = {};
taskStatusMap[Task.Status.Available] = "Available";
taskStatusMap[Task.Status.Blocked] = "Blocked";
taskStatusMap[Task.Status.Completed] = "Completed";
taskStatusMap[Task.Status.Dropped] = "Dropped";
taskStatusMap[Task.Status.DueSoon] = "DueSoon";
taskStatusMap[Task.Status.Next] = "Next";
taskStatusMap[Task.Status.Overdue] = "Overdue";

// Project status enum to string mapping
var projectStatusMap = {};
projectStatusMap[Project.Status.Active] = "Active";
projectStatusMap[Project.Status.Done] = "Done";
projectStatusMap[Project.Status.Dropped] = "Dropped";
projectStatusMap[Project.Status.OnHold] = "OnHold";

// Normalize user-provided status strings to canonical form
var statusNameMap = {
    // Task statuses
    "available": "Available",
    "Available": "Available",
    "blocked": "Blocked",
    "Blocked": "Blocked",
    "completed": "Completed",
    "Completed": "Completed",
    "dropped": "Dropped",
    "Dropped": "Dropped",
    "duesoon": "DueSoon",
    "DueSoon": "DueSoon",
    "due_soon": "DueSoon",
    "next": "Next",
    "Next": "Next",
    "overdue": "Overdue",
    "Overdue": "Overdue",
    // Project statuses
    "active": "Active",
    "Active": "Active",
    "done": "Done",
    "Done": "Done",
    "onhold": "OnHold",
    "OnHold": "OnHold",
    "on_hold": "OnHold",
    "On Hold": "OnHold"
};
