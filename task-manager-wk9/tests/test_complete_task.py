"""Tests for completing tasks and the legacy "done" status (BUG-17 fix)."""

from datetime import date

from app.models import TaskStatus
from app.services import tasks as task_service
from app.services.stats import task_summary


def test_complete_task_sets_status_completed(app):
    """complete_task stores COMPLETED, not the legacy DONE value."""
    task = task_service.create_task(title="Write report")

    result = task_service.complete_task(task.id)

    assert result.status == TaskStatus.COMPLETED
    assert task_service.get_task(task.id).status == TaskStatus.COMPLETED


def test_complete_endpoint_returns_completed(client):
    """POST /tasks/<id>/complete responds with status "completed"."""
    task_id = client.post("/tasks", json={"title": "Write report"}).get_json()["id"]

    resp = client.post(f"/tasks/{task_id}/complete")

    assert resp.status_code == 200
    assert resp.get_json()["status"] == TaskStatus.COMPLETED


def test_update_task_converts_done_to_completed(app):
    """update_task stores the legacy DONE value as COMPLETED."""
    task = task_service.create_task(title="Buy milk")

    result = task_service.update_task(task.id, status=TaskStatus.DONE)

    assert result.status == TaskStatus.COMPLETED


def test_patch_with_done_is_converted_to_completed(client):
    """PATCH /tasks/<id> with status "done" stores and returns "completed"."""
    task_id = client.post("/tasks", json={"title": "Buy milk"}).get_json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"status": "done"})

    assert resp.status_code == 200
    assert resp.get_json()["status"] == TaskStatus.COMPLETED
    listed = client.get("/tasks", query_string={"status": "completed"}).get_json()
    assert [t["id"] for t in listed] == [task_id]


def test_update_task_leaves_other_statuses_unchanged(app):
    """Statuses other than DONE are stored as given."""
    task = task_service.create_task(title="Write report")

    result = task_service.update_task(task.id, status=TaskStatus.IN_PROGRESS)

    assert result.status == TaskStatus.IN_PROGRESS


def test_overdue_count_excludes_completed_tasks(app):
    """A completed task with a past due date is not counted as overdue."""
    today = date(2026, 11, 5)
    past = "2026-11-01"
    open_task = task_service.create_task(title="Still open", due_date=past)
    done_task = task_service.create_task(title="Finished", due_date=past)
    task_service.complete_task(done_task.id)

    summary = task_summary(today=today)

    assert summary["overdue"] == 1
    assert summary["completed"] == 1
    assert task_service.get_task(open_task.id).status == TaskStatus.TODO
