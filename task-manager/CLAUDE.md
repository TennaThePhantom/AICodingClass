# Task Manager - CLAUDE.md

Flask API for tasks and users, in-memory dict storage no database.

## Commands
- install: `pip install -r requirements.txt`
- run tests: `pytest -v`
- run full test file: `pytest tests/test_tasks.py -v`
- run app: `python app.py`  (serves on http://localhost:5000, routes under `/api`)
- run tests quietly: `pytest -q`

## Architecture
- layered: `routes/api.py` -> `services/*.py` -> in-memory dicts (`TASKS`, `USERS`)
- routes are thin HTTP wrappers only, no business logic in `routes/api.py`
- all business logic lives in `services/tasks.py` and `services/users.py`
- errors raised in services are caught by `@api.errorhandler(AppError)` in `routes/api.py`
- canonical example to follow: `services/users.py` (`get_user`, `create_user`)
- entry point: `app.py` registers `routes/api.py` as a Blueprint at `/api`
- boundary: `routes/api.py` must not import `USERS` or `TASKS`. all data access goes through `services/users.py` and `services/tasks.py`. canonical example of a route calling a service is `set_notification_pref_route` in `routes/api.py`

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
- do not modify `utils/errors.py`, `AppError`, `NotFoundError` and `ValidationError` are the shared contract used by `routes/api.py`'s error handler, add new subclasses only if genuinely needed
- do not change function signatures in `services/tasks.py` or `services/users.py`, callers in `routes/api.py` and `tests/` depend on them
- do not bypass `services/` from `routes/api.py`, routes must call services never touch `TASKS` or `USERS` dicts directly
- do not move the `/api` URL prefix out of `app.py`
- do not add business logic or `USERS` / `TASKS` access to `routes/api.py`. routes must call `services/users.py` and `services/tasks.py`. this was the SA-3 boundary in the Task 2 notification subagent pipeline
- do not modify `services/users.py` from a subagent whose scope is `routes/api.py`. cross layer edits break the one subagent one layer decomposition used in Task 2
- do not create scratch test files outside `tests/`. inline verification with `python -c` or Flask test clients is fine, files are not