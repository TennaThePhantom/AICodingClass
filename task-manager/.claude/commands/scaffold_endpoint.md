# Scaffold a new API endpoint. Use when adding a whole new resource; do not use for modifying existing endpoints.

## Goal
Parse $ARGUMENTS as `<resource> <http-method>` Create a new endpoint for
the resource using the specified HTTP method. You must create or update
three things
1. routes/api.py — add the route handler with @api.route(...).
2. services/<resource>.py — add the service function. Create the file if
   it does not exist, following services/users.py as the template.
3. tests/test_<resource>.py — add at least one test that hits the route
   through Flask's test client and asserts the expected status code.

If the resource already exists, extend the existing files instead of
creating new ones.

## Context
- canonical route pattern: routes/api.py (get_task_route,
  update_task_priority_route, set_notification_pref_route).
- canonical service pattern: services/users.py (get_user, create_user).
- appError hierarchy: utils/errors.py (AppError, NotFoundError,
  ValidationError).
- The blueprint is registered at /api in app.py, so routes are exposed at
  /api/<resource>.

## Constraints
- Do not put business logic in the route handler. Routes read the request,
  call one service function, and return jsonify(...).
- Do not raise raw exceptions. Use NotFoundError("Resource") for missing
  records and ValidationError("field", "reason") for bad input.
- do not touch utils/errors.py or app.py.
- do not modify services/users.py.
- HTTP status codes: POST -> 201, GET -> 200, PATCH -> 200, DELETE -> 204.
- every new service function needs type hints and a Google-style docstring.

## Verification
1 - run `pytest -q`. All existing tests must still pass.
2 - write and run a Flask test-client check that hits / api/<resource> with
   the given method and asserts the expected happy-path status code.
3 - Report both outputs.