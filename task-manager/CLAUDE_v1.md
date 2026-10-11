# Task Manager CLAUDE.md (v1) The first one

Flask API for tasks and users
In-memory dict storage no database

## Commands
- install: `pip install -r requirements.txt`
- Run tests: `pytest -v`
- run full test file: `pytest tests/test_tasks.py -v`
- Run app: `python app.py`  (serves on http://localhost:5000, routes under `/api`)

## Architecture
- layered: `routes/api.py` -> `services/*.py` -> in-memory dicts (`TASKS` `USERS`)
- routes are thin HTTP wrappers only no business logic in `routes/api.py`
- all business logic lives in `services/tasks.py` and `services/users.py`
- errors raised in services are caught by `@api.errorhandler(AppError)` in `routes/api.py`.
- example to follow: `services/users.py` (`get_user`, `create_user`)
- Entry point: `app.py` registers `routes/api.py` as a Blueprint at `/api`

## Conventions
- Type hints required on every function signature (params and return)
- google-style docstrings required: `Args:`, `Returns:`, `Raises:` sections
- follow `services/users.py` exactly for style `get_user` is the reference
- Raise `AppError` subclasses from `utils/errors.py` never `Exception`,
  `KeyError`, or `ValueError` directly.
  - missing record -> `raise NotFoundError("Task")` or `NotFoundError("User")`
  - Bad input -> `raise ValidationError("field_name", "reason")`
- every service function must be covered by a test in `tests/`

## Do not touch
- do not modify `utils/errors.py` `AppError`, `NotFoundError`, and
  `ValidationError` are the shared contract used by `routes/api.py`'s
  error handler add new subclasses only if genuinely needed.
- do not change function signatures in `services/tasks.py` or
  `services/users.py` callers in `routes/api.py` and `tests/` depend on them.
- do not bypass `services/` from `routes/api.py` routes must call services
  never touch `TASKS` or `USERS` dicts directly
- do not move the `/api` URL prefix out of `app.py`