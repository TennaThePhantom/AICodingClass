# Task Manager - CLAUDE.md

Flask API for tasks and users, in-memory dict storage no database.

## Commands
- install: `pip install -r requirements.txt`
- run tests: `pytest -v`
- run full test file: `pytest tests/test_tasks.py -v`
- run app: `python app.py`  (serves on http://localhost:5000, routes under `/api`)
- run tests quietly: `pytest -q`
- `/audit_errors <file>`: replaces raw exceptions in a service file with `AppError` subclasses (idempotent, skips correct functions, runs pytest after each)
- `/scaffold_endpoint <resource> <method>`: creates a new API endpoint (service + route + test) following `routes/api.py` and `services/users.py`
- `/sync_response_fields <route-file>`: audits route responses against the fields their service functions return

## Architecture
- layered: `routes/api.py` -> `services/*.py` -> in-memory dicts (`TASKS`, `USERS`)
- routes are thin HTTP wrappers only, no business logic in `routes/api.py`
- all business logic lives in `services/tasks.py` and `services/users.py`
- errors raised in services are caught by `@api.errorhandler(AppError)` in `routes/api.py`
- canonical example to follow: `services/users.py` (`get_user`, `create_user`)
- entry point: `app.py` registers `routes/api.py` as a Blueprint at `/api`
- boundary: `routes/api.py` must not import `USERS` or `TASKS`. all data access goes through `services/users.py` and `services/tasks.py`. canonical example of a route calling a service is `set_notification_pref_route` in `routes/api.py`

## Hooks
This project uses a PreToolUse hook (`.claude/hooks/guard_writes.py`) registered in `.claude/settings.json` for `Write|Edit|MultiEdit|Bash` - It has three guards
- path guard: blocks writes to `utils/errors.py`, `.env`, and `.claude/settings.json` (matches case-insensitively, resolves `..` and symlinks via `realpath`)
- bash guard: blocks destructive commands (`DROP TABLE`, `TRUNCATE TABLE`, `rm -rf`, `git push --force`) and any bash command that references a protected path (like `echo hello > utils/errors.py`)
- content guard: blocks writes to `services/tasks.py` if the content contains `postgresql://` or `sqlite:///`, connection strings must come from environment variables
- To add a new rule - add the path to `BLOCKED_PATHS`, the regex to `BASH_BLOCKED_PATTERNS`, or the file/pattern to `CONTENT_GUARDED_FILES` in `guard_writes.py` - then verify with a local terminal test before restarting claude code. note - `C:\task-manager` is a directory junction to the real project path (used to avoid spaces in the hook command), if you edit the script edit it at `C:\task-manager\.claude\hooks\guard_writes.py` or the real path under `College stuff\...`

## Conventions
- type hints required on every function signature (params and return)
- google-style docstrings required: `Args:`, `Returns:`, `Raises:` sections
- follow `services/users.py` exactly for style, `get_user` is the reference
- raise `AppError` subclasses from `utils/errors.py`, never `Exception`, `KeyError` or `ValueError` directly
  - missing record -> `raise NotFoundError("Task")` or `NotFoundError("User")`
  - bad input -> `raise ValidationError("field_name", "reason")`
- every service function must be covered by a test in `tests/` and tests must assert specific `AppError` subclasses
- every task must belong to an existing user. call `get_user(user_id)` at the start of any function that takes a `user_id` do not touch `TASKS` before this check
- when a function raises a specific `AppError` subclass its test must assert that same subclass, `pytest.raises(NotFoundError)` not `pytest.raises(Exception)`

## Do not touch
- do not change function signatures in `services/tasks.py` or `services/users.py`, callers in `routes/api.py` and `tests/` depend on them
- do not bypass `services/` from `routes/api.py`, routes must call services never touch `TASKS` or `USERS` dicts directly
- do not move the `/api` URL prefix out of `app.py`
- do not add business logic or `USERS` / `TASKS` access to `routes/api.py`. routes must call `services/users.py` and `services/tasks.py`. this was the SA-3 boundary in the Task 2 notification subagent pipeline
- do not modify `services/users.py` from a subagent whose scope is `routes/api.py`. cross layer edits break the one subagent one layer decomposition used in Task 2
- do not create scratch test files outside `tests/`. inline verification with `python -c` or Flask test clients is fine, files are not