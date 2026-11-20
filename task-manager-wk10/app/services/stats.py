"""Summary statistics for the dashboard."""

from collections import Counter
from datetime import date

from app.models import Task, TaskStatus


def _is_overdue(task, today):
    return (
        task.due_date is not None and task.due_date < today and task.status != TaskStatus.COMPLETED
    )


def task_summary(today=None):
    """Return counts by status, the completion rate, and the number of overdue tasks."""
    if today is None:
        today = date.today()
    tasks = Task.query.all()
    total = len(tasks)
    by_status = Counter(task.status for task in tasks)
    completed = by_status[TaskStatus.COMPLETED]

    return {
        "total": total,
        "todo": by_status[TaskStatus.TODO],
        "in_progress": by_status[TaskStatus.IN_PROGRESS],
        "completed": completed,
        "overdue": sum(1 for task in tasks if _is_overdue(task, today)),
        "completion_rate": round(100 * completed / total, 1) if total else 0.0,
    }
