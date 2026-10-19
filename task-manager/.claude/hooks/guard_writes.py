"""PreToolUse hook: blocks writes to protected files, destructive Bash commands, and hardcoded connection strings."""
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

BLOCKED_PATHS = [
    "utils/errors.py",
    ".env",
    ".claude/settings.json",
]

BASH_BLOCKED_PATTERNS = [
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE is destructive"),
    (re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE), "TRUNCATE TABLE is destructive"),
    (re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b"), "rm -rf is destructive"),
    (re.compile(r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b"), "git push --force rewrites history"),
]

CONTENT_GUARDED_FILES = ["services/tasks.py"]
FORBIDDEN_CONTENT_PATTERNS = [
    (re.compile(r"\bpostgresql://"), "hardcoded postgresql:// connection string"),
    (re.compile(r"\bsqlite:///"), "hardcoded sqlite:/// connection string"),
]


def is_path_blocked(file_path: str) -> tuple[bool, str]:
    if not file_path:
        return False, ""
    target = os.path.normcase(os.path.realpath(os.path.join(PROJECT_ROOT, file_path)))
    for pattern in BLOCKED_PATHS:
        protected = os.path.normcase(os.path.realpath(os.path.join(PROJECT_ROOT, pattern)))
        if target == protected:
            return True, f"Protected file: {pattern}"
    return False, ""

def is_bash_blocked(command: str) -> tuple[bool, str]:
    if not command:
        return False, ""
    for regex, reason in BASH_BLOCKED_PATTERNS:
        if regex.search(command):
            return True, reason
    cmd_lower = command.lower().replace("\\", "/")
    for pattern in BLOCKED_PATHS:
        if pattern.lower() in cmd_lower:
            return True, f"Command references protected file: {pattern}"
    return False, ""

def is_content_blocked(file_path: str, content: str) -> tuple[bool, str]:
    if not file_path or not content:
        return False, ""
    target = os.path.normcase(os.path.realpath(os.path.join(PROJECT_ROOT, file_path)))
    for target_file in CONTENT_GUARDED_FILES:
        protected = os.path.normcase(os.path.realpath(os.path.join(PROJECT_ROOT, target_file)))
        if target == protected:
            for regex, reason in FORBIDDEN_CONTENT_PATTERNS:
                if regex.search(content):
                    return True, reason
    return False, ""


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    tool = payload.get("tool_name", "")
    ti = payload.get("tool_input", {})

    if tool == "Bash":
        cmd = ti.get("command", "")
        blocked, reason = is_bash_blocked(cmd)
        if blocked:
            print(f"BLOCKED: {reason}.", file=sys.stderr)
            sys.exit(2)
        sys.exit(0)

    if tool in ("Write", "Edit", "MultiEdit"):
        path = ti.get("file_path") or ti.get("path", "")
        blocked, reason = is_path_blocked(path)
        if blocked:
            print(f"BLOCKED: {reason}.", file=sys.stderr)
            sys.exit(2)

        content = ti.get("content") or ti.get("new_string") or ""
        if "edits" in ti:
            content = "\n".join(e.get("new_string", "") for e in ti["edits"] if isinstance(e, dict))
        blocked, reason = is_content_blocked(path, content)
        if blocked:
            print(f"BLOCKED: {reason}. Use environment variables.", file=sys.stderr)
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()