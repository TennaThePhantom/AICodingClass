import copy
import pytest
from app import app
from services.tasks import TASKS

@pytest.fixture
def restore_tasks():
    snapshot = copy.deepcopy(TASKS)
    yield
    TASKS.clear()
    TASKS.update(snapshot)

@pytest.fixture
def client():
    return app.test_client()

def test_post_task_with_due_date(client, restore_tasks):
    resp = client.post("/api/tasks",
                       json={"title": "x", "user_id": 1, "due_date": "2026-12-25"})
    assert resp.status_code == 201
    assert resp.get_json()["due_date"] == "2026-12-25"

def test_post_task_without_due_date(client, restore_tasks):
    resp = client.post("/api/tasks", json={"title": "x", "user_id": 1})
    assert resp.status_code == 201
    assert resp.get_json()["due_date"] is None

def test_post_task_invalid_due_date(client, restore_tasks):
    resp = client.post("/api/tasks",
                       json={"title": "x", "user_id": 1, "due_date": "12/25/2026"})
    assert resp.status_code == 422
    assert "due_date" in resp.get_json()["error"]

def test_patch_task_due_date_only(client, restore_tasks):
    resp = client.patch("/api/tasks/1", json={"due_date": "2026-12-25"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["due_date"] == "2026-12-25"
    assert body["priority"] == 3

def test_patch_task_priority_and_due_date(client, restore_tasks):
    resp = client.patch("/api/tasks/1", json={"priority": 5, "due_date": "2026-12-25"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["priority"] == 5
    assert body["due_date"] == "2026-12-25"

def test_patch_task_neither_field(client, restore_tasks):
    resp = client.patch("/api/tasks/1", json={})
    assert resp.status_code == 422

def test_patch_task_invalid_due_date(client, restore_tasks):
    resp = client.patch("/api/tasks/1", json={"due_date": "2026-13-01"})
    assert resp.status_code == 422
    assert TASKS[1]["due_date"] is None

def test_get_tasks_overdue(client, restore_tasks):
    TASKS[1]["done"] = False
    TASKS[1]["due_date"] = "2000-01-01"   # past, not done -> overdue
    TASKS[2]["due_date"] = "2999-12-31"   # future
    TASKS[3]["due_date"] = "2000-01-01"   # past but done
    resp = client.get("/api/tasks?overdue=true")
    assert resp.status_code == 200
    assert {task["id"] for task in resp.get_json()} == {1}

def test_get_tasks_overdue_false_returns_all(client):
    resp = client.get("/api/tasks?overdue=false")
    assert resp.status_code == 200
    assert {task["id"] for task in resp.get_json()} == {1, 2, 3}

def test_get_tasks_overdue_invalid_value(client):
    resp = client.get("/api/tasks?overdue=maybe")
    assert resp.status_code == 422

def test_get_tasks_no_params_returns_all(client):
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    assert {task["id"] for task in resp.get_json()} == {1, 2, 3}
