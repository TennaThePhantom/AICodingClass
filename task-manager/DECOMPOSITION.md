# DECOMPOSITION.md  -  Task 2: Notification preference system

## Feature

A user can set a notification preference: `email`, `sms`, or `none` (default
`none`). The preference is stored on the `USERS` record. Two new endpoints
handle read and update, and existing user endpoints must include the new
field in their responses.

Split into four subagents along layer boundaries: data → service → API → tests.
Each subagent runs in a fresh Claude Code session (`/clear` or relaunch between
them). `pytest -q` is run after each subagent, and the result is recorded next
to that subagent's Output field.

## Subagent table

### SA-1: Data layer  -  add `notification_pref` to user records

| Field | Value |
|---|---|
| **Input** | `services/users.py`, `utils/errors.py` |
| **Task** | Add a `notification_pref` key (default `"none"`) to each entry in the `USERS` dict and to records written by `create_user`. |
| **Output** | Modified `services/users.py` only. |
| **Constraint** | Do not touch `routes/api.py`, `services/tasks.py`, `tests/test_tasks.py`, or `app.py`. Do not add new functions  -  only extend the dict shape and `create_user`. |
| **Hand-off** | `USERS` records now have `notification_pref: str`. `create_user` returns records that include the new key. |

**pytest -q result:** 17 passed in 0.02s

---

### SA-2: Service layer  -  add `get_notification_pref` and `set_notification_pref`

| Field | Value |
|---|---|
| **Input** | `services/users.py`, `utils/errors.py` |
| **Task** | Add two functions: `get_notification_pref(user_id: int) -> str` and `set_notification_pref(user_id: int, pref: str) -> dict`. `set_notification_pref` must raise `ValidationError("notification_pref", "...")` if `pref` is not in `{"email", "sms", "none"}`. Both must call `get_user(user_id)` first so unknown users raise `NotFoundError("User")`. |
| **Output** | Modified `services/users.py` only. |
| **Constraint** | Do not touch `routes/api.py` or `tests/`. Do not modify `get_user` or `create_user` (SA-1 shaped them). Follow the existing `create_user` validation style and Google-style docstring pattern. |
| **Hand-off** | Two new callable functions with frozen names and signatures. SA-3 imports them by name. |

**pytest -q result:** 17 passed in 0.02s

---

### SA-3: API layer  -  add PATCH and GET notification routes

| Field | Value |
|---|---|
| **Input** | `routes/api.py`, `services/users.py`, `utils/errors.py` |
| **Task** | Add `PATCH /users/<int:user_id>/notifications` (body: `{"notification_pref": "..."}`) and `GET /users/<int:user_id>/notifications`. PATCH calls `set_notification_pref`, GET calls `get_notification_pref`. The existing `get_user_route` will already include `notification_pref` since the dict has the key  -  verify. |
| **Output** | Modified `routes/api.py` only. |
| **Constraint** | Do not touch `services/` (call the SA-2 functions as-is). Do not add business logic to routes  -  validation and errors live in services. Do not modify `create_task_route`, `update_task_priority_route`, `list_tasks_route`, or `get_task_route`. |
| **Hand-off** | Two new routes registered on the `api` Blueprint. Existing routes still work. |

**pytest -q result:** 17 passed in 0.02s

---

### SA-4: Tests  -  cover notification preference behavior

| Field | Value |
|---|---|
| **Input** | `tests/test_tasks.py` (for style and the `restore_tasks` fixture pattern), `services/users.py`, `routes/api.py` |
| **Task** | Add tests for `set_notification_pref` and `get_notification_pref`: valid update (`email`, `sms`, `none`), invalid value raises `ValidationError`, unknown user raises `NotFoundError`, and `create_user` writes the default `"none"`. Use `pytest.raises(ValidationError)` and `pytest.raises(NotFoundError)`  -  not `pytest.raises(Exception)`. |
| **Output** | New file `tests/test_users.py`. |
| **Constraint** | Do not modify any file in `services/` or `routes/`. Do not modify the existing `tests/test_tasks.py`. Tests must import functions, not reimplement them. |
| **Hand-off** | `pytest -q` passes with new tests covering notification preference behavior. |

**pytest -q result:** 23 passed in 0.03s

---
## Divergence

### Did Claude follow the constraint field for every subagent?

Yes  -  all four. SA-1 touched only `services/users.py`, SA-2 touched only
`services/users.py`, SA-3 touched only `routes/api.py`, and SA-4 created
only `tests/test_users.py`. No cross-layer edits happened. Each subagent
also opened with a `pytest -q` baseline run and ended with a second run,
which matches the pattern established in Task 1. The strongest signal was
SA-3: it imported `set_notification_pref` and `get_notification_pref` from
`services.users` and did not re-implement any logic in the route, even
though the prompt didn't spell out "do not duplicate the service logic."
It also reused the existing `ValidationError("body", ...)` pattern from
`update_task_priority_route` without being told to.

### Did any subagent's output break the next subagent's assumption?

No. SA-1 gave `USERS` records a `notification_pref` key, which SA-2 read
directly with `user["notification_pref"]`. SA-2 produced two functions
with the exact names and signatures SA-3 imported. SA-3 registered two
routes with the exact paths SA-4's tests exercise indirectly through the
services. The only ordering-sensitive detail was the shared `USERS` dict:
SA-4 handled it by adding an opt-in `restore_users` fixture (copied from
`tests/test_tasks.py`'s `restore_tasks`) and by running the suite once
with `test_users.py` first to confirm no leakage in either direction.

### Would you write the decomposition differently a second time?

I would keep the four-way split. Running four fresh sessions cost more
time than a single session would have, but the cost was small compared to
the benefit: each layer stayed reviewable on its own, and every subagent's
diff fit in one screen. The one change I would make is that SA-1 and SA-2
both edited `services/users.py` in separate sessions, which meant SA-2
had to re-read the file to see SA-1's changes. On a second pass I would
merge them into one "service layer" subagent, so the file is opened once.
That said, keeping them separate made the data-shape change (the new key)
explicit and independently testable before SA-2 built on top of it, so
the tradeoff is close. Three subagents (services, routes, tests) would
likely be the sweet spot.

