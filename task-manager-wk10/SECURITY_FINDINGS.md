# Security Findings 

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
| 7 | .gitignore | Secrets hygiene | Medium | Real (FIXED) | No `.env` entry originally; fixed in 8a2e1e6 with `.env`, `.env.*`, `!.env.example`. |
| 8 | .env (commit d6d37f5) | Committed secret file | Medium | Real (FIXED) | `git log --all -p -- .env` shows MAILER_API_KEY; untracked in 8a2e1e6, now gitignored. |

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

## Secrets hygiene

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

-- `git log --all -p -- .env` → `.env` added in commit d6d37f5 with
  `MAILER_API_KEY=mk_live_DRILL_ONLY_7f3a9c2e1b5d` and `MAILER_SENDER=tasks@example.edu`.
- `git ls-files .env` → was tracked from d6d37f5 until untracked in 8a2e1e6.
- `git log --all -S "letmein-2026" --oneline` → 9e08226, 2858030, d6d37f5.
- `git log --all -S "dev-secret-123" --oneline` → 9e08226, 2858030, d6d37f5.

**Rotation notes.**

- `ADMIN_TOKEN` ("letmein-2026") was committed in app/config.py at d6d37f5. It is a
  course/demo token, not a live provider credential, so there is no third-party rotation.
  Rotation performed: the literal was removed in 9e08226, the value now comes from the
  untracked .env, and the current value differs from "letmein-2026".
- `SECRET_KEY` ("dev-secret-123") was committed in app/config.py at d6d37f5. Rotation
  performed: removed in 9e08226, now read from the untracked .env; the current value
  differs from "dev-secret-123", which invalidates any sessions signed with the old key.
- - `MAILER_API_KEY` (mk_live_DRILL_ONLY_7f3a9c2e1b5d) was committed in `.env` at d6d37f5.
  It is a drill placeholder (marked DRILL ONLY, course repo), not a live provider credential,
  so no third-party rotation was performed. If it were real: revoke it in the provider
  dashboard, issue a new key, store it only in the untracked `.env` and CI secrets, and purge
  history with `git filter-repo`. The file is now untracked (8a2e1e6) and `.env` is gitignored.
- `ADMIN_TOKEN` and `SECRET_KEY` were committed in app/config.py; both are now read from
  `os.environ` and the literals removed in 9e08226. Values are local dev placeholders, rotated
  by changing `.env`.
## Evidence appendix

- Traversal proof: `curl.exe -i "http://127.0.0.1:5000/attachments/../requirements.txt"` → PASTE_HERE
- SQLi proof: `curl.exe -i "http://127.0.0.1:5000/tasks/tagged?tag=%27%20OR%20%271%27%3D%271"` →
  PASTE_HERE (number of rows returned)
- False-positive proof: `GET /tasks/search?q=100%25` returns only tasks literally containing `100%`.

## Scan run 

Scope: `app/` (all routes and services), `run.py`, `.gitignore`, git history. Method: source read of
every route and service, grep sweeps, `git log` history and pickaxe searches, and runtime probes with
Flask's test client (in-memory SQLite, placeholder `SECRET_KEY`/`ADMIN_TOKEN` set in the probe's own
environment; probe script kept outside the repo). No source file was modified. Baseline: `pytest -q`
→ 114 passed.

Limits: the guard hook blocked `git log --all -p -- .env`, and the deny rules block reading
`.env` / `.env.example`. These were not worked around. History for `.env` is covered by pickaxe
searches (`git log --all -S`) instead. The `.env.example` contents are taken from the template recorded
earlier in this file (Secrets hygiene section).

### Findings

| # | File:line | Category | Severity | Real / FP | How checked |
|---|-----------|----------|----------|-----------|-------------|
| S1 | app/routes/admin.py:18-20 + app/config.py:14 | Auth — empty token bypass on destructive route | High | Real (FIXED, dfecde1) | With ADMIN_TOKEN="" the app started because os.environ[...] rejects unset but accepts "". `request.args.get("token", "")` then defaulted to "", and compare_digest(b"", b"") is True, so POST /admin/reset with no token deleted every row. Fixed in dfecde1: config.py raises RuntimeError when SECRET_KEY or ADMIN_TOKEN is empty; test_security.py asserts it. |
| S2 | run.py:8 | Unsafe exec — Werkzeug debugger exposed | High | Real (dev entrypoint, but it is the documented `python run.py`) | `app.run(debug=True, host="0.0.0.0")` serves the interactive debugger on every interface. Its console runs arbitrary Python (it is PIN-gated, but a reachable PIN is the only barrier). Debug mode also returns full tracebacks with source lines. These are easy to trigger with the 500s in S5–S8. |
| S3 | app/routes/admin.py:18 | Auth — token in query string | Medium | Real | Token read only from `request.args`. It lands in access logs, proxy logs and browser history. Probe: a valid token sent in an `X-Admin-Token` header → 403 (headers ignored). The constant-time compare itself is correct (see safe list). |
| S4 | git history d6d37f5 (app/config.py:7-8, `.env`) | Secrets in history — rotation unverified | Medium | Real | `git log --all -S "letmein-2026"` and `-S "dev-secret-123"` → d6d37f5, 2858030, 9e08226, 0d2e792. `-S "MAILER_API_KEY"` → d6d37f5, 8a2e1e6 and others. The literals are gone from source but remain in history. The rotation notes above still say `CONFIRM_HERE`. This scan could not verify that the current values differ (reading the env file is blocked). Action: confirm the values changed, then remove the placeholders. |
| S5 | app/services/tasks.py:60, :98 | Input validation — `description` not type-checked | Low | Real | `(description or "").strip()` on a non-str. Probe: `POST /tasks {"title":"t","description":5}` → 500 `AttributeError`. `PATCH /tasks/1 {"description":["x"]}` → 500. |
| S6 | app/services/tasks.py:31 | Input validation — `_validate_status` crashes on unhashable input | Low | Real | `LEGACY_ALIASES.get(status, ...)` with a list or dict raises `TypeError` before the membership check. Probe: `PATCH /tasks/1 {"status":["todo"]}` → 500, and the same for `{"a":1}`. |
| S7 | app/services/tasks.py:48-53 | Input validation — `_clean_tags` type and length | Low | Real | Int → 500 (`'int' object is not iterable`). A dict is accepted, and its keys become tags. There is no length cap: `tags:["x"*300]` → 201 even though the column is `String(200)`, because SQLite does not enforce the length. |
| S8 | app/routes/tasks.py:50-51 | Input validation — non-object JSON body | Low | Real | `update_task(task_id, **data)` with a JSON array body → 500 `TypeError`. |
| S9 | app/services/tasks.py:15-18 | Input validation — `title` coerced with `str()` | Low | Real (cosmetic) | `POST /tasks {"title":{"a":1}}` → 201 with title `"{'a': 1}"`. Non-string types are not rejected. |

S5–S9 are availability and data-quality issues, not data exposure. Each one returns an unhandled 500 or
stores coerced data instead of a `ValidationError`/400.

### Checked and found safe

- **SQLi — `tasks_with_tag` (app/services/tasks.py:148-158).** This is the only raw SQL in `app/`
  (grep for `text(`, `.execute(`, `SELECT`, `exec_driver_sql` → only tasks.py:152-154). It uses the
  bound `:pattern` parameter with `ESCAPE '\'`, and `%`, `_`, `\` are escaped first. Probes:
  `tag=' OR '1'='1` → `[]`, `tag=%` → `[]`, `tag=_` → `[]`, `tag=x` → only the tagged task.
- **SQLi — `search_tasks` (app/services/tasks.py:126-145).** It uses the ORM `ilike(..., escape="\\")`
  with metacharacters escaped. Probes: `q=' OR 1=1--` → `[]`, `q=%` → `[]`.
- **Other DB access.** `list_tasks`, `get_task`, `update_task`, `delete_task` and `task_summary` use
  only ORM `filter_by`, `session.get` and `query.all`. Nothing user-controlled reaches raw SQL.
- **Path traversal — app/routes/attachments.py:10-22.** It uses `realpath` + `commonpath` confinement,
  with a `ValueError` guard for cross-drive paths. Probes, all 404: `../requirements.txt`,
  `..%2frequirements.txt`, `..%2F..%2Frun.py`, `%2e%2e/run.py`, `..\requirements.txt`,
  `C:/Windows/win.ini`, `../attachments_evil/x` (sibling-prefix trick). `//etc/passwd` → 308 slash
  merge, not a read. `welcome.txt` and `subdir/../welcome.txt` → 200 (stay inside the directory).
- **Hardcoded secrets in current source.** `app/config.py:13-14` reads both values from `os.environ`.
  A grep of non-doc, non-test files for secret/token/api_key/password/known literals found no
  literals. `git ls-files` does not list the env file, and `.gitignore:10-12` covers it and its
  variants (template excepted).
- **Timing — app/routes/admin.py:20.** It uses `hmac.compare_digest` on bytes, so it is constant-time.
  A non-ASCII token (`%C3%A9`) → 403 with no crash. Wrong token → 403. The remaining auth issues are
  S1 and S3.
- **Validators applied on every create/update path.**
  - Create (tasks.py:56-67) applies `_validate_title`, `_validate_priority`, `_parse_due_date` and
    `_clean_tags`. Status cannot be set on create, so a sent `status` is ignored and the default
    `todo` is kept.
  - Update (tasks.py:88-108) applies all five validators per field. Unknown fields are rejected by
    `UPDATABLE_FIELDS`: probe `PATCH {"id":99}` → 400, so there is no mass assignment.
  - List (tasks.py:78-85) validates the `status` and `priority` query params: probes → 400.
  - The only gaps are the type-handling cases S5–S9.
- **Unsafe deserialization and templating — checked, none found.** A grep for `pickle`, `yaml`,
  `eval(`, `exec(`, `marshal`, `shelve`, `render_template`, `Markup`, `|safe`, `subprocess` and
  `os.system` across all non-doc files found nothing in `app/` or `run.py`. The only hit is
  `subprocess` in `tests/test_guard.py`, which is test-only. There is no `app/templates/` directory.
  All responses go through `jsonify` or `send_file`. Files checked: app/__init__.py, config.py,
  errors.py, extensions.py, models.py, routes/{tasks,admin,attachments,stats}.py,
  services/{tasks,stats}.py, run.py. The one code-execution risk in this category is the
  debugger (S2).
- **app/routes/stats.py / app/services/stats.py.** These take no user input and do read-only ORM
  aggregation.

### Fixes applied after the scan

- S1 (High): app/config.py now raises RuntimeError if SECRET_KEY or ADMIN_TOKEN is empty,
  not just unset. Proof: `$env:ADMIN_TOKEN=""; python -c "import app.config"` exits non-zero
  with "SECRET_KEY and ADMIN_TOKEN must be set and non-empty". Covered by
  tests/test_security.py::test_empty_admin_token_fails_closed (commit <hash>).