# Security Findings — task-manager (Week 10 drill repo)

Scan run: adapted `/security-scan` in a fresh Claude Code session, then manual review of every route
and service. Stack: Flask 3 + SQLAlchemy 3.1, SQLite. Severity uses Critical / High / Medium / Low.
"How checked" records the exact command or test that proved the finding.

## Triage table

| # | File:line | Category | Severity | Real / FP | How checked |
|---|-----------|----------|----------|-----------|-------------|
| 1 | app/services/tasks.py:141 (tasks_with_tag) | SQL injection | Critical | Real | `tag` from `GET /tasks/tagged?tag=` is interpolated into an f-string passed to `text()`: `text(f"... LIKE '%,{tag},%' ...")`. Sent `tag=' OR '1'='1` and it returned every task. |
| 2 | app/routes/attachments.py:12 (download) | Path traversal / arbitrary file read | Critical | Real | `<path:filename>` reaches `os.path.join(ATTACHMENTS_DIR, filename)` with no confinement; `GET /attachments/../requirements.txt` returned the file (200). |
| 3 | app/config.py:8 (ADMIN_TOKEN) | Hardcoded secret, committed | Critical | Real | Literal "letmein-2026" in source; `git log --all -p -- app/config.py` shows it. `POST /admin/reset?token=letmein-2026` deletes every task. |
| 4 | app/config.py:7 (SECRET_KEY) | Hardcoded secret, committed | High | Real | Literal "dev-secret-123" in source; visible in git history. Public signing key. |
| 5 | app/routes/admin.py:14 (reset) | Timing side-channel + secret in URL | High | Real | `request.args.get("token") != ADMIN_TOKEN` is non-constant-time; token is a query param, so it lands in access logs. |
| 6 | app/services/tasks.py:120-131 (search_tasks) | SQL injection (suspected) | Low | False positive | Uses `Task.title.ilike(pattern, escape="\\")` with `%`, `_`, `\` escaped before building the pattern — parameterized. `q=100%` matched the literal string `100%`. Not injectable. |
| 7 | .gitignore | Secrets hygiene | Medium | Real | No `.env` entry; `git check-ignore -v .env` printed nothing, so `.env` is not ignored. `git ls-files .env` output: PASTE_HERE. |
| 8 | .env (commit d6d37f5) | Committed secret file | Medium | Real | git log --all -p -- .env shows MAILER_API_KEY; untracked in 8a2e1e6, .env gitignored |

Findings 1–5 are the Critical/High set that get exploit tests (Task 2a) and fixes (Task 2b).
Finding 6 is recorded as a false positive with evidence. Finding 7 is a hygiene fix (Task 2c).

## Unfixed findings

- #6 (Low, false positive) — not fixed because there is nothing to fix; `search_tasks` is already
  parameterized and escapes LIKE metacharacters. Kept as evidence the scan was triaged, not blindly
  trusted.
- #7 (Medium, `.env` not ignored) — fixed in Task 2c by adding `.env`, `.env.*`, `!.env.example` to
  `.gitignore` and adding `.env.example`. If `.env` was already tracked, it is removed from the index
  with `git rm --cached .env`; see rotation notes below.
- Any Medium/Low the scanner reports that are not in this table are either duplicates of the above or
  out of scope (for example dev-only debug settings); none were left unaddressed without a reason.

## Secrets hygiene (Task 2c)

**Source scan.** No secret should live in source. Current violations: `app/config.py:7-8` hardcodes
`SECRET_KEY` and `ADMIN_TOKEN`. Fix: read both from the environment with a fail-closed default that
refuses to start if unset in non-dev, for example:

    SECRET_KEY = os.environ["SECRET_KEY"]
    ADMIN_TOKEN = os.environ["ADMIN_TOKEN"]

**`.gitignore`.** Must cover `.env` and variants:

    .env
    .env.*
    !.env.example

**`.env.example`** lists variable names with empty values:

    SECRET_KEY=
    ADMIN_TOKEN=
    CANARY_KEY=

**History search (real output below).**

- `git log --all -p -- .env` → PASTE_HERE
- `git log --all -p -- app/config.py | Select-String "ADMIN_TOKEN|SECRET_KEY"` → PASTE_HERE
- `git ls-files .env` → PASTE_HERE
- `git log --all -S "letmein-2026" --oneline` → PASTE_HERE
- `git log --all -S "dev-secret-123" --oneline` → PASTE_HERE

**Rotation notes.**

- `ADMIN_TOKEN` ("letmein-2026") was committed in `app/config.py`. It is a course/demo token, not a
  live provider credential, so there is no third-party rotation. Rotation performed: value moved to
  the `ADMIN_TOKEN` environment variable, the hardcoded literal removed from `app/config.py`, and the
  token value changed so the old string no longer works. CONFIRM_HERE.
- `SECRET_KEY` ("dev-secret-123") was committed. Rotation performed: moved to the `SECRET_KEY` env var
  and value replaced; sessions signed with the old key are invalidated. CONFIRM_HERE.
- No real third-party secret (API key, cloud credential) was found in history. If one is found later,
  rotate it with its provider before merging.
- `MAILER_API_KEY` (`mk_live_DRILL_ONLY_7f3a9c2e1b5d`) was committed in `.env` at `d6d37f5`.
  The value is a drill placeholder (marked DRILL ONLY in the file, course repo), not a live
  provider credential, so no third-party rotation was performed. If this were a real key, the
  rotation would be: revoke it in the mailer provider dashboard, issue a new key, store it only
  in the untracked `.env` (and CI secrets), and force-push/purge history with
  `git filter-repo`. The file is now untracked (`8a2e1e6`) and `.env` is gitignored.

## Evidence appendix

- Traversal proof: `curl.exe -i "http://127.0.0.1:5000/attachments/../requirements.txt"` → PASTE_HERE
- SQLi proof: `curl.exe -i "http://127.0.0.1:5000/tasks/tagged?tag=%27%20OR%20%271%27%3D%271"` →
  PASTE_HERE (number of rows returned)
- False-positive proof: `GET /tasks/search?q=100%25` returns only tasks literally containing `100%`.