# Audit a service file for missing AppError handling. Use when a services/*.py file still raises raw exceptions; do not use on routes or tests.

## Goal
Audit $ARGUMENTS for missing AppError handling For every function that
raises a raw exception (KeyError, ValueError, TypeError, or a bare
Exception), replace it with the appropriate AppError subclass from
utils/errors.py. If a function already uses AppError correctly, skip it —
do not rewrite it.

## Context
- canonical pattern: services/users.py (`get_user` and `create_user`).
- appError hierarchy: utils/errors.py (AppError, NotFoundError, ValidationError).
- missing record -> `raise NotFoundError("Task")` or `NotFoundError("User")`.
- bad input -> `raise ValidationError("field_name", "reason")`.
- Each function needs type hints and a Google-style docstring with
  Args:, Returns:, and Raises: sections.

## Constraints
- only modify $ARGUMENTS. Do not touch utils/errors.py, routes/api.py,
  services/users.py, tests/test_tasks.py, or tests/test_users.py.
- do not add new AppError subclasses — use only what exists in
  utils/errors.py.
- Preserve every existing function signature exactly. Callers in
  routes/api.py and tests/ depend on them.
- Do not modify the TASKS or USERS dict shapes.

## Verification
After every function you update, run `pytest -q` All existing tests must
still pass before you move to the next function Do not batch the tests at
the end. At the very end, report the final pytest -q output.