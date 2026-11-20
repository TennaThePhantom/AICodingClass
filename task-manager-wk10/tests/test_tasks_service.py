"""Unit tests for app/services/tasks.py (Drill 1, Phase A reference)."""

from datetime import date

import pytest

from app.errors import NotFoundError, ValidationError
from app.models import TaskStatus
from app.services import tasks as svc

# ---------- create_task ----------


def test_create_task_defaults(app):
    task = svc.create_task("Buy milk")
    assert task.id is not None
    assert task.title == "Buy milk"
    assert task.description == ""
    assert task.priority == "medium"
    assert task.status == TaskStatus.TODO
    assert task.due_date is None


def test_create_task_strips_title_and_description(app):
    task = svc.create_task("  Buy milk  ", description="  2 litres  ")
    assert task.title == "Buy milk"
    assert task.description == "2 litres"


@pytest.mark.parametrize("bad", [None, "", "   "])
def test_create_task_requires_title(app, bad):
    with pytest.raises(ValidationError, match="title is required"):
        svc.create_task(bad)


def test_create_task_title_at_max_length_is_allowed(app):
    task = svc.create_task("x" * svc.MAX_TITLE_LENGTH)
    assert len(task.title) == svc.MAX_TITLE_LENGTH


def test_create_task_title_over_max_length_is_rejected(app):
    with pytest.raises(ValidationError, match="at most"):
        svc.create_task("x" * (svc.MAX_TITLE_LENGTH + 1))


def test_create_task_rejects_unknown_priority(app):
    with pytest.raises(ValidationError, match="priority"):
        svc.create_task("Task", priority="urgent")


def test_create_task_parses_iso_due_date(app):
    task = svc.create_task("Task", due_date="2026-12-01")
    assert task.due_date == date(2026, 12, 1)


def test_create_task_accepts_date_object(app):
    task = svc.create_task("Task", due_date=date(2026, 12, 1))
    assert task.due_date == date(2026, 12, 1)


def test_create_task_empty_due_date_means_none(app):
    assert svc.create_task("Task", due_date="").due_date is None


@pytest.mark.parametrize("bad", ["12/01/2026", "2026-13-01", "tomorrow", 20261201])
def test_create_task_rejects_bad_due_date(app, bad):
    with pytest.raises(ValidationError, match="YYYY-MM-DD"):
        svc.create_task("Task", due_date=bad)


# ---------- get_task ----------


def test_get_task_returns_task(app):
    created = svc.create_task("Task")
    assert svc.get_task(created.id).title == "Task"


def test_get_task_missing_raises_not_found(app):
    with pytest.raises(NotFoundError, match="999"):
        svc.get_task(999)


# ---------- list_tasks ----------


def test_list_tasks_oldest_first(app):
    a = svc.create_task("A")
    b = svc.create_task("B")
    assert [t.id for t in svc.list_tasks()] == [a.id, b.id]


def test_list_tasks_filters_by_priority(app):
    svc.create_task("Low", priority="low")
    high = svc.create_task("High", priority="high")
    assert [t.id for t in svc.list_tasks(priority="high")] == [high.id]


def test_list_tasks_filters_by_status(app):
    a = svc.create_task("A")
    svc.create_task("B")
    svc.update_task(a.id, status=TaskStatus.IN_PROGRESS)
    assert [t.id for t in svc.list_tasks(status=TaskStatus.IN_PROGRESS)] == [a.id]


def test_list_tasks_rejects_unknown_status(app):
    with pytest.raises(ValidationError, match="status"):
        svc.list_tasks(status="archived")


def test_list_tasks_rejects_unknown_priority(app):
    with pytest.raises(ValidationError, match="priority"):
        svc.list_tasks(priority="urgent")


# ---------- update_task ----------


def test_update_task_changes_fields(app):
    task = svc.create_task("Old")
    svc.update_task(
        task.id,
        title=" New ",
        description=" d ",
        priority="high",
        due_date="2026-11-30",
        status=TaskStatus.IN_PROGRESS,
    )
    task = svc.get_task(task.id)
    assert task.title == "New"
    assert task.description == "d"
    assert task.priority == "high"
    assert task.due_date == date(2026, 11, 30)
    assert task.status == TaskStatus.IN_PROGRESS


def test_update_task_none_description_becomes_empty(app):
    task = svc.create_task("T", description="x")
    assert svc.update_task(task.id, description=None).description == ""


def test_update_task_can_clear_due_date(app):
    task = svc.create_task("T", due_date="2026-11-30")
    assert svc.update_task(task.id, due_date=None).due_date is None


def test_update_task_rejects_unknown_field(app):
    task = svc.create_task("T")
    with pytest.raises(ValidationError, match="cannot update"):
        svc.update_task(task.id, owner="sam")


def test_update_task_rejects_bad_status(app):
    task = svc.create_task("T")
    with pytest.raises(ValidationError, match="status"):
        svc.update_task(task.id, status="archived")


def test_update_task_missing_raises_not_found(app):
    with pytest.raises(NotFoundError):
        svc.update_task(999, title="x")


# ---------- complete_task ----------


def test_complete_task_marks_task_finished(app):
    task = svc.create_task("T")
    svc.complete_task(task.id)
    # Updated in Drill 2 (BUG-17): this test used to pin the buggy value "done".
    assert svc.get_task(task.id).status == TaskStatus.COMPLETED


def test_legacy_done_status_is_stored_as_completed(app):
    task = svc.create_task("T")
    assert svc.update_task(task.id, status="done").status == TaskStatus.COMPLETED


def test_complete_task_missing_raises_not_found(app):
    with pytest.raises(NotFoundError):
        svc.complete_task(999)


# ---------- delete_task ----------


def test_delete_task_removes_it(app):
    task = svc.create_task("T")
    svc.delete_task(task.id)
    with pytest.raises(NotFoundError):
        svc.get_task(task.id)


def test_delete_task_missing_raises_not_found(app):
    with pytest.raises(NotFoundError):
        svc.delete_task(999)
