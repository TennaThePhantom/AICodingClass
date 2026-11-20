"""Tests for search_tasks and GET /tasks/search (Drill 1, Phase B). Written before the code."""

import pytest

from app.errors import ValidationError
from app.services import tasks as svc


def test_search_matches_title_case_insensitively(app):
    match = svc.create_task("Write REPORT")
    svc.create_task("Buy milk")
    assert [t.id for t in svc.search_tasks("report")] == [match.id]


def test_search_matches_description(app):
    match = svc.create_task("Errand", description="pick up the dry cleaning")
    svc.create_task("Other")
    assert [t.id for t in svc.search_tasks("Dry Clean")] == [match.id]


def test_search_returns_newest_first(app):
    older = svc.create_task("report draft")
    newer = svc.create_task("report final")
    assert [t.id for t in svc.search_tasks("report")] == [newer.id, older.id]


def test_search_ignores_surrounding_whitespace(app):
    match = svc.create_task("Write report")
    assert [t.id for t in svc.search_tasks("  report  ")] == [match.id]


def test_search_with_no_match_returns_empty_list(app):
    svc.create_task("Write report")
    assert svc.search_tasks("vacation") == []


@pytest.mark.parametrize("bad", ["", "   ", None])
def test_search_rejects_empty_query(app, bad):
    with pytest.raises(ValidationError, match="query"):
        svc.search_tasks(bad)


def test_search_treats_percent_and_underscore_literally(app):
    match = svc.create_task("Grow revenue 50%")
    svc.create_task("Grow revenue 500")
    svc.create_task("file_name cleanup")
    svc.create_task("filename cleanup")
    assert [t.id for t in svc.search_tasks("50%")] == [match.id]
    assert [t.title for t in svc.search_tasks("file_name")] == ["file_name cleanup"]


def test_search_route_returns_matches(client):
    client.post("/tasks", json={"title": "Write report"})
    client.post("/tasks", json={"title": "Buy milk"})
    response = client.get("/tasks/search?q=report")
    assert response.status_code == 200
    assert [t["title"] for t in response.get_json()] == ["Write report"]


def test_search_route_without_q_returns_400(client):
    response = client.get("/tasks/search")
    assert response.status_code == 400
    assert "query" in response.get_json()["error"]
