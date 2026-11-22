# REFLECTION.md — PA10

## 1 Most serious finding and how it got into the code
The worst one was the SQL injection in `tasks_with_tag` in `app/services/tasks.py`.
The tag parameter went straight into an f-string inside `text()`. I wrote an exploit
test that sent `tag=' OR '1'='1` and it returned both tasks in the database. That's
the proof in `tests/test_security.py`. The reason it was there is simple the function
built a LIKE pattern by hand instead of binding a parameter and CLAUDE.md didn't say
anything about raw SQL. The fix itself was written by Claude Code, I gave it the
failing test and told it not to touch `tests/` and it rewrote the function with a
bound `pattern` parameter. I reviewed the diff and ran the tests myself, I didn't
hand-write the fix.

The path traversal in `attachments.download` was close behind. The `<path:filename>`
converter got joined to `ATTACHMENTS_DIR` with nothing stopping it, so
`/attachments/../requirements.txt` returned the file with a 200. I didn't write either
of these, they were in the drill code when I started PA10. But they were still there
because no earlier work had security tests and no rule said "don't do this." The
hardcoded `ADMIN_TOKEN` and `SECRET_KEY` in `config.py` were the same kind of thing.
Convenient literals, no rule against them. Commit 2858030 has the failing tests,
9e08226 has the fixes.

## 2 Which guardrail mattered most, and which gave false confidence

The exploit tests mattered most. They were five failing tests that proved the attacks
worked, and after the fix commit they stayed green as regression protection. I
checked that the fix commit didn't touch `tests/` with `git diff --stat`, and it
didn't.

The deny rules and the PreToolUse hook (commit 3842d0a, 55 subprocess tests) are real
guardrails, but they gave me false confidence. When I re-ran the two attacks with them
in place, nothing changed. Both payloads try to write a canary into a new local file
and my guardrails only cover secret reads, network commands, and destructive shell.
So neither layer fired, that was the useful lesson. the hook is only as good as the
list of actions. I think to enumerate, and I missed the one the attack actually uses.

## 3 What I will change about how I use Claude Code on my capstone

Three things, roughly in order of how likely I am to actually do them.

First, write the failing test before the fix. The 2858030 to 9e08226 pair is the
pattern, commit the test while it's red, then fix without editing it. It's the only
part of this project that made a real difference.

Second, treat anything in `docs/` or `attachments/` as data. In both runs, Claude
rendered the injected note as `[passage omitted]` and didn't say the file had an
instruction in it The only time it mentioned the injection was when I asked it to
confirm it hadn't written anything. If I'd stopped after the first answer, I'd never
have known the file was weaponized So I'll ask for that kind of check, or quote the 
instructions myself.

Third, keep secrets out of source. The `.env` - `.env.example` - `load_dotenv` setup
(commit 614bd92) is the pattern I'll copy. I'll also stop treating, "Claude didn't do
the bad thing" as proof the setup is safe. In both runs the model declined the
injection but that was the model's judgment not a guardrail, and it didn't say
anything until I asked.