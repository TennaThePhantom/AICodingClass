import copy
from datetime import date
import pytest
from services.tasks import (process_order, get_task, get_tasks_for_user, create_task,
                            update_task_priority, get_all_tasks, get_tasks_by_priority,
                            get_overdue_tasks, TASKS)
from utils.errors import NotFoundError, ValidationError

@pytest.fixture
def restore_tasks():
    snapshot = copy.deepcopy(TASKS)
    yield
    TASKS.clear()
    TASKS.update(snapshot)

def test_process_order_valid():
    result = process_order(1)
    assert result["done"] is True

def test_process_order_invalid():
    with pytest.raises(NotFoundError):
        process_order(999)

def test_get_task_valid():
    result = get_task(2)
    assert result["title"] == "Write report"

def test_get_task_invalid():
    with pytest.raises(NotFoundError):
        get_task(999)

def test_get_tasks_for_user_valid():
    result = get_tasks_for_user(1)
    assert {task["id"] for task in result} == {1, 2}
    assert all(task["user_id"] == 1 for task in result)

def test_get_tasks_for_user_invalid():
    with pytest.raises(NotFoundError):
        get_tasks_for_user(999)

def test_create_task_default_priority(restore_tasks):
    result = create_task("x", 1)
    assert result["priority"] == 3

def test_create_task_explicit_priority(restore_tasks):
    result = create_task("x", 1, 5)
    assert result["priority"] == 5

def test_create_task_invalid_priority():
    with pytest.raises(ValidationError):
        create_task("x", 1, 0)

def test_create_task_unknown_user():
    with pytest.raises(NotFoundError):
        create_task("x", 999)

def test_update_task_priority_valid(restore_tasks):
    result = update_task_priority(1, 5)
    assert result["priority"] == 5
    assert get_task(1)["priority"] == 5

def test_update_task_priority_invalid():
    with pytest.raises(ValidationError):
        update_task_priority(1, 6)
    assert get_task(1)["priority"] == 3

def test_update_task_priority_unknown_task():
    with pytest.raises(NotFoundError):
        update_task_priority(999, 2)

def test_get_tasks_by_priority_filters(restore_tasks):
    update_task_priority(2, 5)
    assert {task["id"] for task in get_tasks_by_priority(5)} == {2}
    assert {task["id"] for task in get_tasks_by_priority(3)} == {1, 3}

def test_get_tasks_by_priority_empty(restore_tasks):
    for task_id in TASKS:
        TASKS[task_id]["priority"] = 1
    assert get_tasks_by_priority(5) == []

def test_get_tasks_by_priority_invalid():
    with pytest.raises(ValidationError):
        get_tasks_by_priority(99)

def test_get_all_tasks():
    result = get_all_tasks()
    assert {task["id"] for task in result} == {1, 2, 3}

# --- due dates -------------------------------------------------------------

INVALID_DUE_DATES = ["2026/11/01", "11-01-2026", "2026-1-5", "20261101",
                     "2026-02-30", "", 123]

def test_create_task_with_due_date(restore_tasks):
    result = create_task("x", 1, 3, "2026-12-25")
    assert result["due_date"] == "2026-12-25"
    assert get_task(result["id"])["due_date"] == "2026-12-25"

def test_create_task_due_date_keyword(restore_tasks):
    result = create_task("x", 1, due_date="2026-12-25")
    assert result["priority"] == 3
    assert result["due_date"] == "2026-12-25"

def test_create_task_default_due_date(restore_tasks):
    result = create_task("x", 1)
    assert result["due_date"] is None

@pytest.mark.parametrize("bad", INVALID_DUE_DATES)
def test_create_task_invalid_due_date(restore_tasks, bad):
    before = set(TASKS)
    with pytest.raises(ValidationError):
        create_task("x", 1, 3, bad)
    assert set(TASKS) == before

def test_create_task_unknown_user_with_due_date():
    with pytest.raises(NotFoundError):
        create_task("x", 999, 3, "2026-12-25")

def test_update_task_due_date_only(restore_tasks):
    result = update_task_priority(1, due_date="2026-12-25")
    assert result["due_date"] == "2026-12-25"
    assert result["priority"] == 3

def test_update_task_priority_and_due_date(restore_tasks):
    result = update_task_priority(1, 5, "2026-12-25")
    assert result["priority"] == 5
    assert result["due_date"] == "2026-12-25"

def test_update_task_neither_field():
    with pytest.raises(ValidationError):
        update_task_priority(1)

@pytest.mark.parametrize("bad", INVALID_DUE_DATES)
def test_update_task_invalid_due_date_no_partial_update(restore_tasks, bad):
    with pytest.raises(ValidationError):
        update_task_priority(1, 5, bad)
    assert get_task(1)["priority"] == 3
    assert get_task(1)["due_date"] is None

def test_update_task_due_date_unknown_task():
    with pytest.raises(NotFoundError):
        update_task_priority(999, due_date="2026-12-25")

def test_get_overdue_tasks(restore_tasks):
    today = date(2026, 11, 1)
    TASKS[1]["done"] = False
    TASKS[1]["due_date"] = "2026-10-31"   # past, not done -> overdue
    TASKS[2]["due_date"] = "2026-11-01"   # due today -> not overdue
    TASKS[3]["due_date"] = "2026-01-01"   # past but done -> not overdue
    future = create_task("future", 1, due_date="2026-11-02")
    no_date = create_task("no date", 1)
    result_ids = {task["id"] for task in get_overdue_tasks(today)}
    assert result_ids == {1}
    assert future["id"] not in result_ids
    assert no_date["id"] not in result_ids

def test_get_overdue_tasks_none_overdue():
    assert get_overdue_tasks(date(2026, 11, 1)) == []

def test_get_overdue_tasks_defaults_to_today(restore_tasks):
    TASKS[1]["done"] = False
    TASKS[1]["due_date"] = "2000-01-01"
    TASKS[2]["due_date"] = "2999-12-31"
    assert {task["id"] for task in get_overdue_tasks()} == {1}
