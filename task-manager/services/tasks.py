from services.users import get_user
from utils.errors import NotFoundError, ValidationError

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1, "priority": 3},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1, "priority": 3},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2, "priority": 3},
}

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
    task = TASKS[task_id]
    task["done"] = True
    return task

def get_task(task_id: int) -> dict:
    return TASKS[task_id]

def create_task(title: str, user_id: int, priority: int = 3) -> dict:
    """Create a new task for a user.

    Args:
        title: The task's title.
        user_id: The unique identifier for the user who owns the task.
        priority: The task's priority, an integer from 1 to 5. Defaults to 3.

    Returns:
        The newly created task record.

    Raises:
        NotFoundError: If no user exists with the given ID.
        ValidationError: If priority is not an integer from 1 to 5.
    """
    get_user(user_id)
    _validate_priority(priority)
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {"id": new_id, "title": title,
                     "done": False, "user_id": user_id, "priority": priority}
    return TASKS[new_id]

def update_task_priority(task_id: int, priority: int) -> dict:
    """Update a task's priority.

    Args:
        task_id: The unique identifier for the task.
        priority: The new priority, an integer from 1 to 5.

    Returns:
        The updated task record.

    Raises:
        NotFoundError: If no task exists with the given ID.
        ValidationError: If priority is not an integer from 1 to 5.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    _validate_priority(priority)
    TASKS[task_id]["priority"] = priority
    return TASKS[task_id]

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
