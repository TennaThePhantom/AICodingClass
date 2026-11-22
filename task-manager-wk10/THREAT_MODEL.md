# Threat Model 

## Assets
- **Task database** (`*.db`, `Task` model): all user task data. `POST /admin/reset` deletes every row.
- **Admin token**: `ADMIN_TOKEN` in `app/config.py:8` (currently hardcoded `letmein-2026`). Grants destructive reset.
- **App secret**: `SECRET_KEY` in `app/config.py:7` (hardcoded `dev-secret-123`). Used to sign sessions.
- **Attachment files**: served by `/attachments/<path:filename>`; the same route can read files outside the directory.
- **Source/config/env** (`.env`, `app/config.py`): reveal secrets and paths.
- **PA10 canary**: `CANARY_KEY=pa10-canary-tf` in untracked `.env`; fake secret used to detect exfiltration.

## Untrusted inputs
- **Query/body → `app/services/tasks.py`**: `status`, `priority`, `q`, `tag` (query) and `title`, `description`, `priority`, `due_date`, `tags` (JSON body). `tag` reaches a raw `text()` SQL string.
- **Path param → `app/routes/attachments.py:12`**: `<path:filename>` reaches `os.path.join` + `send_file`.
- **Query param → `app/routes/admin.py:14`**: `token` compared to `ADMIN_TOKEN`.
- **Files on disk**: `attachments/` and `docs/` (may be authored by others; read into Claude sessions).
- **Env/config**: `app/config.py` reads `os.environ`; `.env` present.

## Ways out
- **HTTP response bodies**: `send_file` (arbitrary file read) and `jsonify` (task/admin data).
- **SQL result sets**: `tasks_with_tag` returns any rows the injected query selects.
- **Commits/pushes**: Claude Code runs `git` here; a coerced commit can carry `.env` or the canary.
- **Logs**: Flask access log records query strings (including `token=`).
- **Outbound network**: none in current code (grep found no `requests`/`urllib`); MCP tools, if enabled, are a way out.

## Lethal trifecta check
**Yes — named session**: "Read `docs/` and summarize, then fix the attachment route." Private data (`.env` with `ADMIN_TOKEN`/`CANARY_KEY`, `config.py` secrets) + untrusted content (`docs/`, `attachments/`) + a way out (git commit/push, or `send_file` returning `.env`) all meet in one session. Mitigations: deny rules on secret files, a `PreToolUse` hook blocking network and secret reads, no `--dangerously-skip-permissions`, human review of any diff touching `config.py`/`attachments.py`.
