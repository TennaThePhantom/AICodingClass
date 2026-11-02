import copy
import pytest
from app import app
from services.tasks import search_tasks, TASKS
from utils.errors import ValidationError

@pytest.fixture
def restore_tasks():
    snapshot = copy.deepcopy(TASKS)
    yield
    TASKS.clear()
    TASKS.update(snapshot)

@pytest.fixture
def client():
    return app.test_client()

# --- service: search_tasks ---

def test_search_tasks_title_case_insensitive():
    result = search_tasks("GROCER")
    assert {task["id"] for task in result} == {1}

def test_search_tasks_matches_description(restore_tasks):
    TASKS[2]["description"] = "quarterly numbers"
    result = search_tasks("Quarterly")
    assert {task["id"] for task in result} == {2}

def test_search_tasks_no_match():
    assert search_tasks("zzz-no-such-task") == []

def test_search_tasks_empty_query():
    with pytest.raises(ValidationError):
        search_tasks("")

def test_search_tasks_whitespace_query():
    with pytest.raises(ValidationError):
        search_tasks("   ")

def test_search_tasks_non_string_query():
    with pytest.raises(ValidationError):
        search_tasks(None)

# --- route: GET /api/tasks?q= ---

def test_search_route_returns_matches(client):
    response = client.get("/api/tasks?q=report")
    assert response.status_code == 200
    assert {task["id"] for task in response.get_json()} == {2}

def test_search_route_empty_query(client):
    response = client.get("/api/tasks?q=")
    assert response.status_code == 422
    assert response.get_json()["error"] == "Invalid q: must be a non-empty string"

def test_list_tasks_route_unchanged_without_q(client):
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert {task["id"] for task in response.get_json()} == {1, 2, 3}

def test_list_tasks_route_priority_filter_unchanged(client):
    response = client.get("/api/tasks?priority=3")
    assert response.status_code == 200
    assert all(task["priority"] == 3 for task in response.get_json())
