"""Business logic for tasks. Routes call these functions; they never query the database directly."""

from datetime import date

from sqlalchemy import text

from app.errors import NotFoundError, ValidationError
from app.extensions import db
from app.models import PRIORITIES, Task, TaskStatus

MAX_TITLE_LENGTH = 120
UPDATABLE_FIELDS = {"title", "description", "priority", "due_date", "status", "tags"}


def _validate_title(title):
    if title is None or not str(title).strip():
        raise ValidationError("title is required")
    title = str(title).strip()
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError(f"title must be at most {MAX_TITLE_LENGTH} characters")
    return title


def _validate_priority(priority):
    if priority not in PRIORITIES:
        raise ValidationError(f"priority must be one of {', '.join(PRIORITIES)}")
    return priority


def _validate_status(status):
    status = TaskStatus.LEGACY_ALIASES.get(status, status)
    if status not in TaskStatus.ALL:
        raise ValidationError(f"status must be one of {', '.join(TaskStatus.ALL)}")
    return status


def _parse_due_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValidationError("due_date must be a date in YYYY-MM-DD format") from None


def _clean_tags(tags):
    if tags is None:
        return ""
    if isinstance(tags, str):
        tags = tags.split(",")
    return ",".join(sorted({str(t).strip().lower() for t in tags if str(t).strip()}))


def create_task(title, description="", priority="medium", due_date=None, tags=None):
    """Create and return a new task."""
    task = Task(
        title=_validate_title(title),
        description=(description or "").strip(),
        priority=_validate_priority(priority),
        due_date=_parse_due_date(due_date),
        tags=_clean_tags(tags),
    )
    db.session.add(task)
    db.session.commit()
    return task


def get_task(task_id):
    """Return the task with this id, or raise NotFoundError."""
    task = db.session.get(Task, task_id)
    if task is None:
        raise NotFoundError(f"task {task_id} not found")
    return task


def list_tasks(status=None, priority=None):
    """Return tasks, optionally filtered by status and priority, oldest first."""
    query = Task.query
    if status is not None:
        query = query.filter_by(status=_validate_status(status))
    if priority is not None:
        query = query.filter_by(priority=_validate_priority(priority))
    return query.order_by(Task.id).all()


def update_task(task_id, **fields):
    """Update the given fields of a task and return it."""
    unknown = set(fields) - UPDATABLE_FIELDS
    if unknown:
        raise ValidationError(f"cannot update field(s): {', '.join(sorted(unknown))}")

    task = get_task(task_id)
    if "title" in fields:
        task.title = _validate_title(fields["title"])
    if "description" in fields:
        task.description = (fields["description"] or "").strip()
    if "priority" in fields:
        task.priority = _validate_priority(fields["priority"])
    if "due_date" in fields:
        task.due_date = _parse_due_date(fields["due_date"])
    if "status" in fields:
        task.status = _validate_status(fields["status"])
    if "tags" in fields:
        task.tags = _clean_tags(fields["tags"])
    db.session.commit()
    return task


def complete_task(task_id):
    """Mark a task as finished and return it."""
    task = get_task(task_id)
    task.status = TaskStatus.COMPLETED
    db.session.commit()
    return task


def delete_task(task_id):
    """Delete a task."""
    task = get_task(task_id)
    db.session.delete(task)
    db.session.commit()


def search_tasks(query):
    """Return tasks whose title or description contains query (case-insensitive), newest first.

    The characters % and _ in the query are matched literally, not as SQL wildcards.
    """
    if query is None or not str(query).strip():
        raise ValidationError("query is required")
    text = str(query).strip()
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    return (
        Task.query.filter(
            db.or_(
                Task.title.ilike(pattern, escape="\\"),
                Task.description.ilike(pattern, escape="\\"),
            )
        )
        .order_by(Task.id.desc())
        .all()
    )


def tasks_with_tag(tag):
    """Return tasks that carry the given tag, oldest first."""
    # Escape LIKE wildcards so the tag is matched literally, then bind it as a parameter.
    escaped = tag.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    rows = db.session.execute(
        text(
            "SELECT id FROM task WHERE ',' || tags || ',' LIKE :pattern ESCAPE '\\' ORDER BY id"
        ),
        {"pattern": f"%,{escaped},%"},
    ).all()
    return [db.session.get(Task, row.id) for row in rows]
