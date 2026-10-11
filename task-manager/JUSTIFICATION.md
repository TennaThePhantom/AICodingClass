# JUSTIFICATION.md

## Commands
I put four commands in because each one is useful. The install command
is `pip install -r requirements.txt` and its the first thing you need because
the project doesn't come with everything already installed. The `pytest -v`
command runs all the tests and that's the main one. I also added
`pytest tests/test_tasks.py -v` because in session 1 claude only needed to run
one file, so it was handy. The `python app.py` line is there, because claude
kept talking about how the api returns 404 or 500 errors, and knowing the
entry point helps it understand that. If I had to cut the file in half, I would
remove the `pytest tests/test_tasks.py -v` line because you can just run
everything with `pytest -v` anyways.

## Architecture
This is about stopping claude from putting logic in the wrong place.
The problem was that `services/tasks.py` had two different styles in it. One
good and one bad so saying "follow the existing pattern" was confusing. In
session 3 claude actually said it wouldn't copy the local functions and pointed
at `services/users.py` instead which shows the rule worked. The line about
`@api.errorhandler(AppError)` is important because, it tells claude that if it
raises `NotFoundError` in a service the route will send back a 404 instead of
crashing. If I had to cut something from this section I would cut the part
about the blueprint, and the `/api` prefix because claude never really needed
to think about that.

## Conventions
This is the section that got two rules got added because of what happened
in the sessions. The rule about calling `get_user(user_id)` was added after
session 2, because claude called it but it was just guessing from `create_user`
and it wasn't told to. That felt risky because a different run might not do it.
The rule about tests using `pytest.raises(NotFoundError)` instead of
`pytest.raises(Exception)` was added after session 1 and session 2 both left
that loose test alone so I figured it needed to be a rule. Session 3 showed
both rules worked because claude said "as CLAUDE.md requires", when it wrote the
new test. If I cut this section in half, I would drop the type hints line
because the docstring and error rules did more work.

## Do not touch
I wrote four rules here and each one is for a real reason. The `utils/errors.py`
rule is because that file is used by the routes and the services both so if
you change it you break the error handler in two spots. The rule
protects the routes and tests, because they import the functions by name. The
rule about not bypassing services is basically the architecture rule again, so
routes cant just grab `TASKS` or `USERS` directly. The `/api` prefix rule is
probably the smallest one and I would cut it first because if someone changed
it the whole app would break right away so its unlikely to happen by accident.

## Team comparison
If three people were working on this I would change two things. First I would
add a rule about when to update CLAUDE.md, because in my three sessions I added
rules in the middle, so its a living file not something you set once. On a team
somebody has to approve rule changes and everyone needs to pull the newest
version before they start. Second I would add a short checklist for code review
that matches the conventions section, because in my sessions claude kept
pointing out that `process_order`, and `get_task` raise raw `KeyError` and, that
some tests use `pytest.raises(Exception)` but it didnt fix them, because that
was out of scope. On a team somebody has to actually follow up on those and a
checklist like "does this match `services/users.py`" and "does the new test
assert a specific `AppError`" would make that easier.