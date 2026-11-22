---
description: Run a security scan of this Flask project against PA10's six categories
---

Scan this repository for security weaknesses and write findings to
`SECURITY_FINDINGS.md`. Do not modify any source file during the scan.

Project facts to use:
- Stack: Flask 3 + SQLAlchemy 3.1, SQLite, JSON API.
- Routes live in `app/routes/` (tasks.py, admin.py, attachments.py, stats.py).
- Business logic and all DB access live in `app/services/`.
- Secrets come from `.env` via `load_dotenv()` in `app/config.py`; the app fails
  closed if `SECRET_KEY` or `ADMIN_TOKEN` is unset.
- Tests are in `tests/`. Guard hook is `.claude/hooks/guard.py`.

Check these six categories. For each finding record: file:line, category, severity
(Critical/High/Medium/Low), real or false positive, and how you checked.

1. SQL injection — any `text()` call, f-string or string concatenation that reaches
   `db.session.execute`, and any raw query. Check `app/services/tasks.py` especially
   (`tasks_with_tag`, `search_tasks`).
2. Path traversal / arbitrary file read — any route that turns user input into a
   filesystem path. Start with `app/routes/attachments.py` (`<path:filename>`).
3. Hardcoded secrets and secrets in history — literals in `app/config.py`, values in
   committed `.env`, `ADMIN_TOKEN` comparisons. Cross-check `git log --all -p -- .env`
   and `git log --all -p -- app/config.py`.
4. Authentication and timing — token checks that are not constant-time
   (`!=` instead of `hmac.compare_digest`), tokens passed in query strings, destructive
   routes reachable with a default or guessable token (`app/routes/admin.py`).
5. Input validation — request bodies and query params that reach services without
   validation. Confirm `_validate_title`, `_validate_priority`, `_validate_status`,
   `_parse_due_date`, `_clean_tags` are actually applied on every create/update path.
6. Unsafe deserialization and templating — `pickle`, `yaml.load` without SafeLoader,
   `eval`/`exec`, and any template rendering of unescaped user data. This stack is a
   JSON API so this category is likely empty; record it as "checked, none found" with
   the files you checked.

Output format: append a new section to `SECURITY_FINDINGS.md` titled
"## Scan run — <date>" with a markdown table of findings, plus a short
"checked and found safe" list with the evidence for each. Do not invent findings;
if a category has none, say so and name the files you looked at.