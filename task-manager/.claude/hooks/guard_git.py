#!/usr/bin/env python3
"""PreToolUse hook: blocks dangerous git commands.

Blocks:
  - git push to main or master
  - git push --force, -f, or --force-with-lease
  - any command using --no-verify
"""
import json
import re
import sys


# Regexes operate on the raw command string. Use word boundaries so
# "git push origin feature/main" does not match "push to main".
PUSH_MAIN = re.compile(
    r"\bgit\s+push\b.*\b(origin\s+)?(main|master)\b",
    re.IGNORECASE,
)
FORCE_PUSH = re.compile(
    r"\bgit\s+push\b.*(\s-f\b|--force\b|--force-with-lease\b)",
    re.IGNORECASE,
)
NO_VERIFY = re.compile(r"(--no-verify\b|\s-n\b)")


def is_blocked(command: str) -> tuple[bool, str]:
    if not command:
        return False, ""
    if PUSH_MAIN.search(command):
        return True, "push to main/master is forbidden"
    if FORCE_PUSH.search(command):
        return True, "force-push is forbidden"
    if NO_VERIFY.search(command):
        return True, "--no-verify is forbidden (skips commit-msg hook)"
    return False, ""


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command = (payload.get("tool_input") or {}).get("command", "")
    blocked, reason = is_blocked(command)
    if blocked:
        print(f"BLOCKED: {reason}.", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()