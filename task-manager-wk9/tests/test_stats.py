"""Characterization tests for task_summary and the GET /stats route.

These pin down the current behavior of app/services/stats.py so it can be refactored safely.
"""

from datetime import date, timedelta

import pytest

from app.extensions import db
from app.models import Task, TaskStatus
from app.services.stats import task_summary

TODAY = date(2026, 6, 15)
YESTERDAY = TODAY - timedelta(days=1)
TOMORROW = TODAY + timedelta(days=1)


def add_task(status=TaskStatus.TODO, due_date=None, title="task"):
    """Insert a task directly into the database and return it."""
    task = Task(title=title, status=status, due_date=due_date)
    db.session.add(task)
    db.session.commit()
    return task


def test_empty_database(app):
    assert task_summary(today=TODAY) == {
        "total": 0,
        "todo": 0,
        "in_progress": 0,
        "completed": 0,
        "overdue": 0,
        "completion_rate": 0.0,
    }


@pytest.mark.parametrize(
    "status, key",
    [
        (TaskStatus.TODO, "todo"),
        (TaskStatus.IN_PROGRESS, "in_progress"),
        (TaskStatus.COMPLETED, "completed"),
    ],
)
def test_single_status_is_counted_in_its_bucket(app, status, key):
    add_task(status=status)

    result = task_summary(today=TODAY)

    assert result["total"] == 1
    assert result[key] == 1
    for other in ("todo", "in_progress", "completed"):
        if other != key:
            assert result[other] == 0


def test_mixed_status_counts(app):
    for _ in range(3):
        add_task(status=TaskStatus.TODO)
    for _ in range(2):
        add_task(status=TaskStatus.IN_PROGRESS)
    add_task(status=TaskStatus.COMPLETED)

    result = task_summary(today=TODAY)

    assert result["total"] == 6
    assert result["todo"] == 3
    assert result["in_progress"] == 2
    assert result["completed"] == 1


def test_legacy_done_status_counts_toward_total_only(app):
    # Current behavior: the legacy "done" value is not counted as completed.
    add_task(status=TaskStatus.DONE)

    result = task_summary(today=TODAY)

    assert result["total"] == 1
    assert result["todo"] == 0
    assert result["in_progress"] == 0
    assert result["completed"] == 0
    assert result["completion_rate"] == 0.0


def test_completion_rate_rounds_to_one_decimal(app):
    add_task(status=TaskStatus.COMPLETED)
    add_task(status=TaskStatus.TODO)
    add_task(status=TaskStatus.IN_PROGRESS)

    assert task_summary(today=TODAY)["completion_rate"] == 33.3


def test_completion_rate_all_completed(app):
    add_task(status=TaskStatus.COMPLETED)
    add_task(status=TaskStatus.COMPLETED)

    assert task_summary(today=TODAY)["completion_rate"] == 100.0


@pytest.mark.parametrize(
    "status, due_date, expected_overdue",
    [
        (TaskStatus.TODO, YESTERDAY, 1),
        (TaskStatus.IN_PROGRESS, YESTERDAY, 1),
        (TaskStatus.TODO, TODAY, 0),
        (TaskStatus.TODO, TOMORROW, 0),
        (TaskStatus.TODO, None, 0),
        (TaskStatus.COMPLETED, YESTERDAY, 0),
        # Current behavior: a past-due legacy "done" task is still counted as overdue.
        (TaskStatus.DONE, YESTERDAY, 1),
    ],
    ids=[
        "todo-due-yesterday",
        "in-progress-due-yesterday",
        "due-today",
        "due-tomorrow",
        "no-due-date",
        "completed-past-due",
        "legacy-done-past-due",
    ],
)
def test_overdue_rules(app, status, due_date, expected_overdue):
    add_task(status=status, due_date=due_date)

    assert task_summary(today=TODAY)["overdue"] == expected_overdue


def test_overdue_counts_multiple_tasks(app):
    add_task(due_date=YESTERDAY)
    add_task(due_date=TODAY - timedelta(days=30))
    add_task(due_date=TODAY)
    add_task(due_date=TOMORROW)
    add_task(due_date=None)
    add_task(status=TaskStatus.COMPLETED, due_date=YESTERDAY)

    assert task_summary(today=TODAY)["overdue"] == 2


def test_default_today_uses_current_date(app):
    real_today = date.today()
    add_task(due_date=real_today - timedelta(days=1))
    add_task(due_date=real_today)
    add_task(due_date=real_today + timedelta(days=1))

    assert task_summary()["overdue"] == 1


def test_stats_route_returns_summary(client):
    add_task(status=TaskStatus.TODO, due_date=date.today() - timedelta(days=1))
    add_task(status=TaskStatus.IN_PROGRESS)
    add_task(status=TaskStatus.COMPLETED)

    response = client.get("/stats")

    assert response.status_code == 200
    assert response.get_json() == {
        "total": 3,
        "todo": 1,
        "in_progress": 1,
        "completed": 1,
        "overdue": 1,
        "completion_rate": 33.3,
    }


def test_stats_route_empty_database(client):
    response = client.get("/stats")

    assert response.status_code == 200
    assert response.get_json()["total"] == 0
    assert response.get_json()["completion_rate"] == 0.0
