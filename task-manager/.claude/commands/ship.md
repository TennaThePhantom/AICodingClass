# Review, test, and commit the current changes. Use when ready to commit; do not use for pushing or merging.

## Goal
Review the current uncommitted changes, validate them, and create one conventional commit. Follow the 4 steps below in order and stop at any step that fails.

## Context
- Commit format from `CLAUDE.md`: `type(scope): subject`, allowed types `feat`, `fix`, `test`, `docs`, `refactor`, `chore`, `perf`, allowed scopes `tasks`, `users`, `api`, `tests`, `hooks`, `commands`, `git`. Subject lowercase, imperative, max 72 chars.
- Work from the project root (`task-manager/`). If you are not in that directory, `cd` there first.

## Constraints
- Do NOT run `git push` or any remote operation.
- Do NOT use `--no-verify` or skip hooks.
- If any check below fails, STOP and report the file + line + problem. Do NOT commit.
- If nothing is staged or changed, STOP and say "nothing to commit".

## Verification
Run the checks in this exact order. Use your Bash tool to run each command yourself.

### Step 1 — Inspect the diff for debug artifacts
Run `git status --short` and `git diff HEAD`. Scan the diff output for:
- `print(` calls
- `breakpoint()` calls
- New `TODO` or `FIXME` comments added in this diff
- Commented-out code blocks (lines starting with `#` that look like disabled code)

If you find any, stop with: "STOP: found <type> at <file>:<line>".

### Step 2 — Run the test suite
Run `pytest -q`. If anything fails, stop and paste the failing test output. Do NOT commit.

### Step 3 — Propose the commit message
Based on the diff, propose **one** conventional commit message in the format `type(scope): subject`. Show it to the user and wait for explicit approval ("yes", "ok", "approve"). If the user says "change to <new message>", use the new one.

### Step 4 — Commit
Only after approval, run `git commit -m "<approved message>"`. Then show `git log --oneline -1` to confirm.

Report the final result at the end.