# MERGE_REPORT.md

## Overview

Two features were developed in parallel worktrees:
- **feat/tasks-keyword-search**: added `search_tasks(query)` to `services/tasks.py` and a `q` branch to `GET /api/tasks` in `routes/api.py`.
- **feat/tasks-due-dates**: added `due_date` field to `create_task` and `update_task_priority`, `_validate_due_date` helper, `get_overdue_tasks()` to `services/tasks.py`, and both `due_date` (POST/PATCH) and `overdue=true` (GET) handling to `routes/api.py`.

Both branches started from commit `11dc6fc` (feat(git): add safety kit and git hooks).

## Merge process

The keyword-search branch merged into `main` via fast-forward (commit `a1b9c17`). No conflict.

The due-dates branch merged via 3-way merge and produced a **content conflict in `routes/api.py`** (two hunks).

## Conflicts and resolutions

### Conflict 1 — the `services.tasks` import block

Feature A added `search_tasks`; Feature B added `get_overdue_tasks`. Git saw two edits to the same import tuple and could not auto-merge.

**Resolution:** Combined both imports into one tuple:

```python
from services.tasks import (get_task, create_task, process_order, update_task_priority,
                            get_all_tasks, get_tasks_by_priority, search_tasks,
                            get_overdue_tasks)
```

**Why:** Both features are additive. Dropping either import would break one of the tests, and we needed to keep both.

### Conflict 2 — `list_tasks_route` body

Feature A wanted to check `q` first. Feature B wanted to check `overdue` first. Git saw two different additions at the top of `list_tasks_route`.

**Resolution:** Stacked both branches inside the same function with an explicit order:

```python
def list_tasks_route():
    # q takes precedence over other filters (documented in MERGE_REPORT.md)
    if "q" in request.args:
        return jsonify(search_tasks(request.args.get("q", "")))

    overdue = request.args.get("overdue")
    if overdue not in (None, "true", "false"):
        raise ValidationError("overdue", "must be true or false")
    if overdue == "true":
        return jsonify(get_overdue_tasks())

    if "priority" not in request.args:
        return jsonify(get_all_tasks())
    priority = request.args.get("priority", type=int)
    return jsonify(get_tasks_by_priority(priority))
```

**Why this order:** We chose `q` first because search is the most specific filter (a free-text query). `overdue` next because it is a boolean flag with explicit validation. `priority` last, matching its original position. A request that sends both `q` and `overdue` will be treated as a search — documented explicitly in the code comment so future readers know this is intentional, not an accidental short-circuit.

## Tests changed

No existing test was weakened or removed. The full test suite still asserts specific `AppError` subclasses (`pytest.raises(ValidationError)` and `pytest.raises(NotFoundError)`), never `pytest.raises(Exception)`.

Two new test files exist as a result of the merge:
- `tests/test_search.py` — 10 tests for keyword search (6 service, 4 route).
- `tests/test_api.py` — new file added by Feature B for the due-date route tests.
- `tests/test_tasks.py` gained due-date service tests.

## Final test output

```
.....................................................................  [100%]
69 passed in 0.27s
```

## Post-merge verification

 ran `pytest -q` after resolving the conflict and before committing the merge. All 69 tests passed. Both feature branches and the merge commit are on `main`. Neither feature branch was deleted they remain as evidence of the parallel workflow.