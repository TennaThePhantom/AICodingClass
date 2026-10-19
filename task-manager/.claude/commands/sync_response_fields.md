# Check that route responses include every field returned by the service. Use after adding a new field to a model; do not use for new endpoints.

## Goal
Audit $ARGUMENTS (a route file or a service file) and verify that every
field returned by the service functions is actually present in the JSON
response the routes send back. For each route handler:
1 - Identify which service function it calls.
2 - Identify the fields that service function returns - (read its body and
   its docstring).
3 - confirm the route's jsonify(...) - call exposes all of those fields.

If a field is missing, add it to the route's response. If a route builds a
custom response shape (e.g. `{"notification_pref": value}`) and that is
intentional, leave it alone and note why.

## Context
- Service functions live in services/tasks.py and services/users.py.
- route handlers live in routes/api.py.
- canonical pattern where route returns the whole service record:
  `get_task_route` and `update_task_priority_route`.
- Canonical pattern where route builds a partial response:
  `get_notification_pref_route` returns `{"notification_pref": value}`.

## Constraints
- do not modify services/ files — only routes/api.py may change.
- do not change any route's HTTP status code.
- Do not rename existing JSON keys — only add missing ones.
- preserve the existing thin-route style- no business logic in the route.
- do not touch utils/errors.py, app.py, or any tests/.

## Verification
Run `pytest -q`. All tests must still pass Then do a manual check by
calling each modified route through Flask's test client and printing the
JSON response, to confirm the new fields appear Report both outputs.