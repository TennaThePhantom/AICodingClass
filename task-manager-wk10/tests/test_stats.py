"""Characterization tests for task_summary, written before refactoring stats.py."""

from datetime import date

from app.models import TaskStatus
from app.services import tasks as svc
from app.services.stats import task_summary

TODAY = date(2026, 11, 4)


def test_summary_of_empty_database(app):
    assert task_summary(today=TODAY) == {
        "total": 0,
        "todo": 0,
        "in_progress": 0,
        "completed": 0,
        "overdue": 0,
        "completion_rate": 0.0,
    }


def test_summary_counts_each_status_and_rate(app):
    svc.create_task("a")
    b = svc.create_task("b")
    c = svc.create_task("c")
    svc.update_task(b.id, status=TaskStatus.IN_PROGRESS)
    svc.complete_task(c.id)
    summary = task_summary(today=TODAY)
    assert summary["total"] == 3
    assert summary["todo"] == 1
    assert summary["in_progress"] == 1
    assert summary["completed"] == 1
    assert summary["completion_rate"] == 33.3


def test_overdue_counts_past_due_unfinished_tasks_only(app):
    svc.create_task("past", due_date="2026-11-03")
    svc.create_task("today", due_date="2026-11-04")
    svc.create_task("future", due_date="2026-11-05")
    svc.create_task("no date")
    done = svc.create_task("past but done", due_date="2026-11-01")
    svc.complete_task(done.id)
    assert task_summary(today=TODAY)["overdue"] == 1


def test_summary_defaults_to_today(app):
    svc.create_task("far past", due_date="2000-01-01")
    assert task_summary()["overdue"] == 1


def test_stats_route(client):
    client.post("/tasks", json={"title": "a"})
    assert client.get("/stats").get_json()["total"] == 1
