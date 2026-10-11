import copy
import pytest
from services.tasks import (process_order, get_task, get_tasks_for_user, create_task,
                            update_task_priority, get_all_tasks, get_tasks_by_priority, TASKS)
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
    with pytest.raises(Exception):
        process_order(999)

def test_get_task_valid():
    result = get_task(2)
    assert result["title"] == "Write report"

def test_get_task_invalid():
    with pytest.raises(Exception):
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
