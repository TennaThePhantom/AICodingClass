"""Task service — task CRUD operations."""

import re
from datetime import date

from services.users import get_user
from utils.errors import NotFoundError, ValidationError

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1, "priority": 3,
        "due_date": None},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1, "priority": 3,
        "due_date": None},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2, "priority": 3,
        "due_date": None},
}

_DUE_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")

def _validate_due_date(due_date: str | None) -> None:
    """Validate a task due date value.

    Args:
        due_date: The due date to check. Must be None or a real calendar date
            as a string in YYYY-MM-DD format.

    Returns:
        None.

    Raises:
        ValidationError: If due_date is not None and not a valid YYYY-MM-DD date string.
    """
    if due_date is None:
        return
    if not isinstance(due_date, str) or not _DUE_DATE_PATTERN.fullmatch(due_date):
        raise ValidationError("due_date", "must be a date string in YYYY-MM-DD format")
    try:
        date.fromisoformat(due_date)
    except ValueError:
        raise ValidationError("due_date", "must be a date string in YYYY-MM-DD format")

def _validate_priority(priority: int) -> None:
    """Validate a task priority value.

    Args:
        priority: The priority to check. Must be an integer from 1 to 5.

    Returns:
        None.

    Raises:
        ValidationError: If priority is not an integer from 1 to 5.
    """
    if isinstance(priority, bool) or not isinstance(priority, int) or not 1 <= priority <= 5:
        raise ValidationError("priority", "must be an integer from 1 to 5")

def process_order(task_id: int) -> dict:
    """Mark a task as done.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The updated task record.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    task = TASKS[task_id]
    task["done"] = True
    return task

def get_task(task_id: int) -> dict:
    """Retrieve a task by ID.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    return TASKS[task_id]

def create_task(title: str, user_id: int, priority: int = 3,
                due_date: str | None = None) -> dict:
    """Create a new task for a user.

    Args:
        title: The task's title.
        user_id: The unique identifier for the user who owns the task.
        priority: The task's priority, an integer from 1 to 5. Defaults to 3.
        due_date: Optional due date as a YYYY-MM-DD string. Defaults to None.

    Returns:
        The newly created task record.

    Raises:
        NotFoundError: If no user exists with the given ID.
        ValidationError: If priority is not an integer from 1 to 5, or due_date
            is not a valid YYYY-MM-DD date string.
    """
    get_user(user_id)
    _validate_priority(priority)
    _validate_due_date(due_date)
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {"id": new_id, "title": title, "done": False, "user_id": user_id,
                     "priority": priority, "due_date": due_date}
    return TASKS[new_id]

def update_task_priority(task_id: int, priority: int | None = None,
                         due_date: str | None = None) -> dict:
    """Update a task's priority and/or due date.

    Both fields are validated before anything is changed, so an invalid value
    never leaves the task partially updated.

    Args:
        task_id: The unique identifier for the task.
        priority: The new priority, an integer from 1 to 5. None leaves it unchanged.
        due_date: The new due date as a YYYY-MM-DD string. None leaves it unchanged.

    Returns:
        The updated task record.

    Raises:
        NotFoundError: If no task exists with the given ID.
        ValidationError: If neither priority nor due_date is given, priority is
            not an integer from 1 to 5, or due_date is not a valid YYYY-MM-DD
            date string.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    if priority is None and due_date is None:
        raise ValidationError("body", "must include priority or due_date")
    if priority is not None:
        _validate_priority(priority)
    _validate_due_date(due_date)
    if priority is not None:
        TASKS[task_id]["priority"] = priority
    if due_date is not None:
        TASKS[task_id]["due_date"] = due_date
    return TASKS[task_id]

def get_overdue_tasks(today: date | None = None) -> list[dict]:
    """Retrieve all unfinished tasks whose due date has passed.

    Args:
        today: The date to compare against. Defaults to the current date.

    Returns:
        A list of task records that are not done and have a due_date strictly
        before today. Tasks without a due_date are never overdue. Empty if none match.
    """
    if today is None:
        today = date.today()
    return [task for task in TASKS.values()
            if not task["done"]
            and task.get("due_date") is not None
            and date.fromisoformat(task["due_date"]) < today]

def get_all_tasks() -> list[dict]:
    """Retrieve all tasks.

    Returns:
        A list of every task record. Empty if there are no tasks.
    """
    return list(TASKS.values())

def get_tasks_by_priority(priority: int) -> list[dict]:
    """Retrieve all tasks with a given priority.

    Args:
        priority: The priority to filter by, an integer from 1 to 5.

    Returns:
        A list of task records with that priority. Empty if none match.

    Raises:
        ValidationError: If priority is not an integer from 1 to 5.
    """
    _validate_priority(priority)
    return [task for task in TASKS.values() if task["priority"] == priority]

def search_tasks(query: str) -> list[dict]:
    """Search tasks by keyword in title or description (case-insensitive).

    Args:
        query: The text to search for. Surrounding whitespace is ignored.

    Returns:
        A list of task records whose title or description contains the query.
        Empty if none match.

    Raises:
        ValidationError: If query is not a string or is empty or whitespace-only.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValidationError("q", "must be a non-empty string")
    needle = query.strip().casefold()
    return [task for task in TASKS.values()
            if needle in task.get("title", "").casefold()
            or needle in task.get("description", "").casefold()]

def get_tasks_for_user(user_id: int) -> list[dict]:
    """Retrieve all tasks belonging to a user.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        A list of the user's task records. Empty if the user has no tasks.

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    get_user(user_id)
    return [task for task in TASKS.values() if task["user_id"] == user_id]

# test line

# test line
