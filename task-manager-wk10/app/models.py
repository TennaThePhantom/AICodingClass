"""Database models."""

from datetime import datetime, timezone

from app.extensions import db


class TaskStatus:
    """Allowed values for Task.status."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

    ALL = (TODO, IN_PROGRESS, COMPLETED)

    # Old spellings still sent by the legacy mobile client, mapped to the current value.
    LEGACY_ALIASES = {"done": COMPLETED}


PRIORITIES = ("low", "medium", "high")


class Task(db.Model):
    """A single to-do item."""

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.String(20), nullable=False, default=TaskStatus.TODO)
    priority = db.Column(db.String(10), nullable=False, default="medium")
    due_date = db.Column(db.Date, nullable=True)
    tags = db.Column(db.String(200), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        """Return a JSON-serializable dict."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "tags": [t for t in self.tags.split(",") if t],
            "created_at": self.created_at.isoformat(),
        }
