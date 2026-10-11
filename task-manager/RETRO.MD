# RETRO.md — Task 3A: Retrospective

## 1. Plan Mode value

Plan Mode earned its keep in Session 3 of Task 1. I asked claude to make a new
GET /tasks route that filters by priority, and I amended the plan to say "if
priority is None, return all tasks." Claude pushed back on my amendment and
said that checking for None would make ?priority=abc return every task
instead of a 422, because request.args.get("priority", type=int) returns None
for both a missing value and a value that isnt a number. So it branched on
"priority not in request.args" instead. If I had approved my own original
amendment the route would have had a real bug that would need a revert and a
replan later. Session 1 had a smaller win too. I amended the plan to add a
step 0 that runs pytest -q before making changes, and even though claude
skipped it that time (see paragraph 2) the step showed up on its own in
Sessions 2, 3 and 4. So the amendment from Session 1 shaped how the rest of
the sessions went even though it wasnt followed in that one.

## 2. Plan Mode limits

The session where the output did not match the amended plan was Session 1.
I amended the plan to add "Step 0: run pytest -q before any changes." When
claude executed, it ran the tests once at the end and skipped the baseline.
The plan said one thing and the execution did another. This tells me the
reliability boundary for Plan Mode is between the plan and the execution
step. The plan is what you approve, but nothing mechanically enforces every
step in it. Verification steps like "run tests first" are exactly the kind
that get quietly dropped when the model is focused on finishing the actual
change. From Session 2 on I started watching for this and by Session 3 the
before and after runs were both happening every time without me asking.

## 3. Subagent value

The subagent boundary that mattered most was SA-3, which kept routes/api.py
separate from services/users.py. In a single session claude would have had
every reason to inline the notification preference validation into the route
handler. The route is the last place the request touches code and its the
easiest place to just add a quick check. Because SA-3's prompt said "call the
existing functions as-is, do not modify anything in services/," claude only
imported set_notification_pref and get_notification_pref and did nothing
else in the service layer. If I had let claude build the whole notification
feature in one session the validation rule `pref in ("email", "sms", "none")`
would have shown up in both the service and the route, and a later refactor
would have had to find and fix both copies.

## 4. Gap analysis

The rule I would most want to enforce mechanically is SA-3's constraint:
"Do not modify anything in services/ from a subagent whose output is scoped
to routes/api.py." A hook that enforces this would run after each subagents
edits and inspect the git diff --name-only output, failing the session if any
file outside the declared Output field was touched. That one check would
catch a cross layer edit before pytest even runs and it would turn the "one
subagent, one layer" promise into something the tool verifies instead of
something I have to notice by reading diffs.