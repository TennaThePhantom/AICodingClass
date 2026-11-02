# WORKFLOW_LOG.md

## Feature A — Keyword Search

**Worktree used:** `.claude/worktrees/feat-search`
**Branch:** `feat/tasks-keyword-search`

### 1. Plan Mode and the change requested
I started Claude Code in Plan Mode (`Shift+Tab`) and gave it the prompt for Feature A. Claude proposed a plan that noticed `GET /api/tasks` already existed and correctly decided to add a `q` branch inside the existing `list_tasks_route` instead of creating a duplicate route.

Before approving, I requested two changes to the plan:
1. Write the failing tests first, so I could capture the red-to-green evidence.
2. Put the new tests in a separate file (`tests/test_search.py`) instead of modifying `tests/test_tasks.py`, to keep the diff clean.

Claude updated the plan to reflect both changes, and I approved it.

### 2. Failing test output
Claude wrote `tests/test_search.py` with 10 tests and ran `pytest -q`. It failed at collection with:
```
ImportError: cannot import name 'search_tasks' from 'services.tasks'
```
This proves the tests were written and failing before any implementation.

### 3. /diff review and corrections
When I ran `/diff`, the changes were limited to the 3 expected files. One thing I corrected during review: I noticed Claude's initial implementation used `query.casefold()` for the search needle but did not apply `.strip()` to the incoming query. I asked Claude to strip whitespace from the query, so `search_tasks("  report  ")` would behave the same as `search_tasks("report")`. Claude updated `search_tasks` to do `query.strip().casefold()`.

### 4. Commit list
- `a1b9c17 feat(tasks): add keyword search to task listing` (3 files: `services/tasks.py`, `routes/api.py`, `tests/test_search.py`)

---

## Feature B — Due Dates and Overdue Filter

**Worktree used:** `.claude/worktrees/feat-due`
**Branch:** `feat/tasks-due-dates`

### 1. Plan Mode and the change requested
I started a second Claude Code session in the `feat-due` worktree and entered Plan Mode. Claude asked two clarifying questions during planning:
1. **PATCH shape:** Should `update_task_priority` require a priority? I chose Option 1 (both optional), so callers can send only `due_date`.
2. **Overdue semantics:** Should completed tasks with past due dates count as overdue? I chose Option 1 (exclude done tasks).

Claude then proposed a plan. Before approving, I requested two changes:
1. Write the failing tests first, so I could capture the red run.
2. Add an exception to `CLAUDE.md` since the feature changes function signatures in `services/tasks.py`, which the existing rule prohibits.

Claude updated the plan to include both changes and I approved it.

### 2. Failing test output
Claude wrote the new tests in `tests/test_tasks.py` and created `tests/test_api.py`. The first `pytest -q` stopped with a collection error because `get_overdue_tasks` did not exist yet. Claude then ran the test files individually and got 9 test failures (missing `due_date` fields, wrong status codes, unfiltered overdue list).

### 3. /diff review and corrections
When I ran `/diff`, the diff contained exactly the 5 expected files. During review, I noticed a test isolation bug: the existing `test_process_order_valid` mutates task 1 to `done=True` without restoring it, so the new overdue tests picked up leftover state. I asked Claude to fix the new overdue tests by setting `done` explicitly in each test using the `restore_tasks` fixture, instead of relying on the default seed data. Claude did this and `pytest -q` went from 9 failed to 59 passed.

### 4. Commit list
- `9a65ed2 feat(tasks): add optional due dates and overdue filter` (5 files: `CLAUDE.md`, `routes/api.py`, `services/tasks.py`, `tests/test_tasks.py`, `tests/test_api.py`)

---

## Merge and Reconciliation

Both feature branches were merged into `main` locally.

- `git merge feat/tasks-keyword-search` completed via fast-forward (commit `a1b9c17`). No conflict.
- `git merge feat/tasks-due-dates` produced a content conflict in `routes/api.py` (both branches added imports and both branches added branches to `list_tasks_route`).

I resolved the conflict manually in VS Code by combining both sides: both imports in the same tuple, and both `q` and `overdue` branches inside `list_tasks_route`, with `q` taking precedence (documented in `MERGE_REPORT.md`). The final merge commit passes all 69 tests.