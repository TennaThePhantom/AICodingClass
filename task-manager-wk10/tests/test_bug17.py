"""Regression test for BUG-17: completed tasks are not counted as completed."""


def test_completed_task_counts_in_stats_and_filter(client):
    task_id = client.post("/tasks", json={"title": "Write report"}).get_json()["id"]
    client.post("/tasks", json={"title": "Buy milk"})

    response = client.post(f"/tasks/{task_id}/complete")
    assert response.status_code == 200
    assert response.get_json()["status"] == "completed"

    stats = client.get("/stats").get_json()
    assert stats["completed"] == 1
    assert stats["completion_rate"] == 50.0

    completed = client.get("/tasks?status=completed").get_json()
    assert [t["id"] for t in completed] == [task_id]
