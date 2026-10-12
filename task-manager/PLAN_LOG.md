# PLAN_LOG.md - Task 1: Priority field

## Supervision Log

| Session # | Prompt summary (≤15 words) | Did you amend the plan? | What you changed | Did output match amended plan? |
|---|---|---|---|---|

| 1 | Add priority to create_task and TASKS dict | Yes | Added step 0 to run pytest -q before changes; added note about routes/api.py staying out of scope; required full before/after pytest output | Partially — Claude ran pytest -q only after the changes, not before, so the step 0 baseline I added in the amendment was skipped. |


| 2 | Add PATCH /tasks endpoint and update_task_priority | Yes | Required full docstring for _validate_priority matching services/users.py; closed the list-body 500 gap with ValidationError("body", ...); removed the scratch Flask test script | Yes |



| 3 | Add GET /tasks?priority filter and get_all_tasks | Yes | Made priority optional by adding get_all_tasks() and branching the route; kept 422 for invalid priority values | Partially — I asked Claude to branch on "priority is None", but Claude branched on "priority not in request.args" instead, because my condition would have made ?priority=abc return all tasks instead of a 422. Claude's version is correct; my amendment had a bug. |


| 4 | Add tests for priority feature with explicit isolation fixture | Yes | Changed autouse fixture to named opt-in fixture requested by mutating tests; added test_get_tasks_by_priority_empty for the empty-result branch | Yes Claude refined the amendment: it made the fixture opt-in only for tests that mutate on the success path, so a leaked mutation on an error path would still be caught by a later test. |