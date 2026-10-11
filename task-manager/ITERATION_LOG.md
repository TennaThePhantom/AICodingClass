# ITERATION_LOG.md

## Session 1 — 2026-9-30


### Prompt used
Add error handling to the process_order function in @services/tasks.py. Do not change the function signature. Run pytest -v when done.


### What Claude did
Claude read `services/tasks.py`, added `from utils.errors import NotFoundError`
at the top of the file, and re-wrote `process_order` to check
`if task_id not in TASKS: raise NotFoundError("Task")` before accessing the
dict. It added a full Google-style docstring with `Args:`, `Returns:`, and
`Raises:` sections and kept the signature as `process_order(task_id: int) -> dict`.
All 4 tests passed with `pytest -v`.

Correct:
- Raised `NotFoundError` from `utils/errors.py` instead of raw `KeyError`.
- added the Google-style docstring with a `Raises:` section.
- Preserved the function signature.
- Ran `pytest -v` at the end and reported 4 passed.

Wrong / incomplete:
- nothing functionally wrong. Claude did, however, point out that
  `test_process_order_invalid` only asserts `pytest.raises(Exception)` so the
  test would still pass even if the wrong error type were raised meaning the
  test does not actually verify the new behavior
  . Claude left it alone because the prompt said "do not change the function signature" and did not ask for test edits.that's correct behavior but it exposes a gap in CLAUDE.md: there is no rule about keeping tests specific when error types change

### Observation
Rules governing this session:
- "Raise `AppError` subclasses from `utils/errors.py` never `Exception`,
  `KeyError`, or `ValueError` directly"
- "Follow `services/users.py` exactly for style — `get_user` is the reference."
- "type hints required on every function signature."
- "Google-style docstrings required: `Args:`, `Returns:`, `Raises:` sections."
- "do not change function signatures in `services/tasks.py` or
  `services/users.py`."

All five rules were followed.
The rule that mattered most was the explicit
`NotFoundError("Task")` example under `## Conventions` which is exactly what
Claude produced. This confirms the "specific example beats generic advice"
principle, naming the file (`utils/errors.py`), the class (`NotFoundError`),
and the argument (`"Task"`) left no room for Claude to invent its own pattern.

The session surfaced one gap, CLAUDE.md tells Claude to raise `AppError`
subclasses but says nothing about updating the test that asserts the error.
`test_process_order_invalid` still uses `pytest.raises(Exception)` so it
would pass even if `process_order` raised the wrong error. This is the kind of
rule the file is currently missing.

### CLAUDE.md update (if any)
No update for this session. All existing rules were followed, and adding a new
rule about test specificity would be premature. I want to see whether the
same gap shows up in Session 2 before adding a rule to fix it. If Session 2
also exposes the test-specificity gap I will add a rule then, so the update is
justified by two sessions of evidence instead of one.

## Session 2 — 2026-10-1

### Prompt used
Refactor create_task in @services/tasks.py to match the style of get_user in @services/users.py exactly. Run pytest -v when done.


### What Claude did
Claude read both `services/tasks.py` and `services/users.py`, then rewrote
`create_task` to match the `get_user` `create_user` pattern. It added a
Google-style docstring with `Args:`, `Returns:`, and `Raises:` sections, and
raised `ValidationError("title", "cannot be empty")` when `title` is blank,
directly mirroring the `name` check in `create_user`. It also added a call to
`get_user(user_id)` at the start of `create_task`, so creating a task for a
nonexistent user now raises `NotFoundError("User")` via `get_user`. The
signature is unchanged, because CLAUDE.md says every service function must be
covered by a test Claude added three new tests to `tests/test_tasks.py`,
a valid create, a blank title, and an unknown user. All 7 tests pass with
`pytest -v`.

Correct:
- google docstring with all three sections, including `Raises:`
- `ValidationError("title", "cannot be empty")` matches the existing
  `create_user` pattern for `name`
- Signature preserved; `routes/api.py` caller unaffected
- Added three tests to satisfy the "every service function must be covered"
  rule
- proactively flagged that `get_task` and `process_order` still raise bare
  `KeyError` and that `create_task_route` reads `data["title"]` directly

Wrong / incomplete:
- Claude's decision to call `get_user(user_id)` was **inferred** not
  instructed. CLAUDE.md never says tasks must belong to a real user Claude
  guessed it from reading `create_user`. That is a lucky inference a less
  careful run could easily have skipped the check
- The existing `test_process_order_invalid` still uses
  `pytest.raises(Exception)` Claude added three new tests, but did not tighten
  this loose assertion This is the second session in a row where that pattern
  went unfixed.

### Observation
Rules governing this session:
- "Google-style docstrings required: `Args:`, `Returns:`, `Raises:` sections
- "raise `AppError` subclasses from `utils/errors.py` — never `Exception`,
  `KeyError`, or `ValueError` directly."
- "bad input -> `raise ValidationError("field_name", "reason")`."
- "every service function must be covered by a test in `tests/`."
- "Do not change function signatures in `services/tasks.py` or
  `services/users.py`."

All rules were followed. The `ValidationError("field_name", "reason")`, example
in CLAUDE.md is what produced the correct `ValidationError("title", ...)` call
without any further prompting. The "every service function must be covered"
rule is what caused Claude to add three tests that were not requested.

Two gaps surfaced

1. **Business-rule inference.** CLAUDE.md says `services/users.py` is the
   canonical pattern but it does not say "creating a task requires an existing
   user." Claude inferred the `get_user(user_id)` check by reading `create_user`
   for its validation style. This is fragile the rule needs to be explicit
   because a future refactor of `create_user` could cause the inference to
   disappear.

2. **Test specificity.** Two sessions in a row, `test_process_order_invalid`
   was left as `pytest.raises(Exception)` even though the code it tests now
   raises a specific `NotFoundError`. The convention rule about tests exists but
   is too vague to catch this.

### CLAUDE.md update
Two rules added under `## Conventions`:

- **Every task must belong to an existing user. Call `get_user(user_id)` at the
  start of any function that takes a `user_id` do not touch `TASKS` before
  this check.*()* Justification Claude inferred this in Session 2 but it was not
  instructed, so a future session could skip it. Making it explicit removes the
  luck.
- **When a function raises a specific `AppError` subclass, its test must assert
  that same subclass** (e.g `pytest.raises(NotFoundError)`, not
  `pytest.raises(Exception)`). Justification, this pattern was left unfixed in
  both Session 1 and Session 2 Two sessions of evidence is enough to justify
  the rule.




## Session 3 — 2026-10-03

### Prompt used
Add a new function to @services/tasks.py that returns all tasks for a given user_id. Follow the same pattern as the existing functions. Add a test for it. Run pytest -v when done.


### What Claude did
Claude read `services/tasks.py` and immediately noted that the existing
functions in that file lack docstrings and raise raw `KeyError` which breaks
the project rules in CLAUDE.md. It chose to model the new function on
`services/users.py` instead, citing CLAUDE.md's designation of that file as
the reference implementation.

It added `get_tasks_for_user(user_id: int) -> list[dict]` to
`services/tasks.py` with -
- a Google-style docstring with `Args:`, `Returns:`, and `Raises:` sections
- a call to `get_user(user_id)` before touching `TASKS`, so an unknown user
  raises `NotFoundError("User")`
- a list comprehension over `TASKS.values()` that filters by `user_id
- Correct type annotations on both the parameter and the return type

It also updated `tests/test_tasks.py` to import `get_tasks_for_user` and
`NotFoundError` and added two tests: -
- `test_get_tasks_for_user_valid`  asserts user 1 gets tasks 1 and 2.
- `test_get_tasks_for_user_invalid`- asserts `pytest.raises(NotFoundError)`.

All 6 tests pass with `pytest -v`.

Correct:
- Followed the `services/users.py` pattern explicitly not the broken local
  functions and said so in its summary.
- applied the "Every task must belong to an existing user" rule by calling
  `get_user(user_id)` at the top of the function and cited the rule when
  explaining why.
- Applied the "tests must assert specific `AppError` subclasses" rule
  used `pytest.raises(NotFoundError)`, and explicitly said "as CLAUDE.md
  Requires"
- added the Google docstring with all three sections.
- ran `pytest -v` and reported 6 passed

Wrong / incomplete:
- Claude again flagged that `create_task` does not check that the user
  exists, even though the new CLAUDE.md rule says it must. The rule exists
  but the existing code does not comply with it. Claude correctly stayed in
  scope and did not silently fix it but the tension is worth recording. A
  newly-added rule does not retroactively fix code that predates it.
- The existing `test_process_order_invalid` and `test_get_task_invalid` still
  use `pytest.raises(Exception)`. Claude noted this but did not change them
  because the prompt did not ask.

### Observation
Rules governing this session:
- "Follows `services/users.py` exactly for style  `get_user` is the reference"
- "Every task must belong to an existing user. Call `get_user(user_id)` at
  the start of any function that takes a `user_id`"  (added - after Session 2)
- "When a function raises a specific `AppError` subclass. its test must assert
  that same subclass `pytest.raises(NotFoundError)` not
  `pytest.raises(Exception)`"  (added - after Session 2)
- "google-style docsrings required: `Args:`, `Returns:` `Raises:` sections."
- "Every service function must be covered by a test in `tests/`."

Every rule that applied was followed, and for the first time, Claude 
quoted CLAUDE.md by name when explaining its choices:

- It said it modeled the function on `services/users.py` "which CLAUDE.md
  designates as the reference implementation."
- It said it called `get_user(user_id)` "before touching `TASKS`" matching
  the wording of the rule added after Session 2.
- it said the invalid test uses `pytest.raises(NotFoundError)` "as CLAUDE.md
  Requires."

comparison to Sessions 1 and 2

- **Session 1** was a single function edit. All rules followed, but no rule
  was *tested* by an ambiguous decision.
- **Session 2** exposed a real gap: Claude called `get_user(user_id)` by
  *inference* from `create_user` not because CLAUDE.md said to. It also left
  a loose `pytest.raises(Exception)` alone and never came back to it.
- **Session 3** exercised both newly-added rules Claude applied them
  correctly **and explicitly referenced them** in its reasoning. It also
  correctly refused to copy the broken local functions using CLAUDE.md's
  own preference for `services/users.py` as the justification.

This is the clearest evidence of improvement across the three sessions.
the same class of decision that was inferred in Session 2 is now being made
*by rule* in Session 3 with the rule cited.

### CLAUDE.md update
No update for this session. All rules were followed, including both rules
added after Session 2. Adding a third update would not be justified by any
observed failure. The one open issue existing code (`create_task`,
`process_order`, `get_task`) that does not comply with the new rules is a
code-quality problem, not a CLAUDE.md problem, and would be addressed by a
followup refactor prompt rather than another rule to go around the issue.