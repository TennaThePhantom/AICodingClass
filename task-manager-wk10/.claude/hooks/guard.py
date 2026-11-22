"""PreToolUse guard hook for Claude Code (PA10 Task 3d).

Reads the hook payload as JSON on stdin. Exits 0 to allow the tool call.
On refusal, prints "Blocked: <reason>" to stderr and exits 2, which Claude Code
treats as a blocking error. Any malformed input is blocked, never allowed.
"""

import json
import re
import sys
from fnmatch import fnmatchcase

SECRET_PATTERNS = [".env", ".env.*", "**/.env", "**/secrets/**"]
MIGRATION_PATTERNS = ["migrations/**", "**/migrations/**", "**/alembic/**"]
PROD_CONFIG_PATTERNS = ["app/config.py", "**/config/production*", "**/*.prod.*"]

# A command word must stand alone: not preceded or followed by a word char, "." or "-".
# That keeps "pytest", "sync", "ssh-keygen" and "curl.txt" from matching.
_WORD = r"(?<![\w.-]){}(?:\.exe)?(?![\w.-])"
NETWORK_RE = re.compile(_WORD.format(r"(curl|wget|nc|ssh|scp)"), re.IGNORECASE)
SQLITE_RE = re.compile(_WORD.format(r"sqlite3"), re.IGNORECASE)
GIT_RM_RE = re.compile(r"(?<![\w.-])git(?:\s+-\S+)*\s+rm(?![\w.-])", re.IGNORECASE)
RM_RE = re.compile(r"(?<![\w.-])rm((?:\s+-\S+)+)", re.IGNORECASE)

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
PATH_KEYS = ("file_path", "path", "notebook_path")


class Blocked(Exception):
    """Raised with a human-readable reason when a tool call must be refused."""


def path_matches(path, patterns):
    """Return the first pattern matching the path (full path, basename or suffix), else None."""
    p = path.strip().strip("'\"").replace("\\", "/").lower()
    while p.startswith("./"):
        p = p[2:]
    if not p:
        return None
    base = p.rstrip("/").rsplit("/", 1)[-1]
    for pat in patterns:
        suffix_pat = "*/" + pat.removeprefix("**/")
        if fnmatchcase(p, pat) or fnmatchcase(base, pat) or fnmatchcase("/" + p, suffix_pat):
            return pat
    return None


def is_rm_rf(command):
    """Return True if the command runs rm with both recursive and force flags."""
    for match in RM_RE.finditer(command):
        flags = match.group(1).split()
        short = "".join(f[1:] for f in flags if not f.startswith("--"))
        recursive = "r" in short.lower() or "--recursive" in flags
        force = "f" in short or "--force" in flags
        if recursive and force:
            return True
    return False


def check(payload):
    """Validate one hook payload and raise Blocked if the tool call is not allowed."""
    if not isinstance(payload, dict):
        raise Blocked("payload is not a JSON object")
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(tool, str):
        raise Blocked("tool_name is missing or not a string")
    if not isinstance(tool_input, dict):
        raise Blocked("tool_input is missing or not an object")

    command = tool_input.get("command", "") if tool == "Bash" else ""
    if not isinstance(command, str):
        raise Blocked("Bash command is not a string")

    paths = [tool_input[k] for k in PATH_KEYS if isinstance(tool_input.get(k), str)]
    if tool == "Glob" and isinstance(tool_input.get("pattern"), str):
        paths.append(tool_input["pattern"])
    tokens = [t for t in re.split(r"[\s<>|;&()`'\"=]+", command) if t]

    # a. Secret files (direct tool paths and paths mentioned in shell commands).
    for candidate in paths + tokens:
        if pat := path_matches(candidate, SECRET_PATTERNS):
            raise Blocked(f"access to secret file '{candidate}' (matches {pat})")
    # b. Network commands.
    if m := NETWORK_RE.search(command):
        raise Blocked(f"network command '{m.group(1)}' is not allowed")
    # c. Destructive commands.
    if is_rm_rf(command):
        raise Blocked("destructive command 'rm -rf' is not allowed")
    if GIT_RM_RE.search(command):
        raise Blocked("destructive command 'git rm' is not allowed")
    if SQLITE_RE.search(command):
        raise Blocked("direct database access via 'sqlite3' is not allowed")
    # d/e. Project rules apply to file edits.
    if tool in EDIT_TOOLS:
        for candidate in paths:
            if pat := path_matches(candidate, MIGRATION_PATTERNS):
                raise Blocked(f"project rule A: migrations are read-only ('{candidate}' ~ {pat})")
            if pat := path_matches(candidate, PROD_CONFIG_PATTERNS):
                raise Blocked(f"project rule B: prod config is read-only ('{candidate}' ~ {pat})")


def main():
    """Entry point: read stdin, run checks, and exit 0 (allow) or 2 (block)."""
    try:
        raw = sys.stdin.buffer.read().decode("utf-8-sig")
        if not raw.strip():
            raise Blocked("empty hook input")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise Blocked(f"invalid JSON input ({exc.msg})") from None
        check(payload)
    except Blocked as exc:
        print(f"Blocked: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # fail closed on anything unexpected
        print(f"Blocked: guard error ({type(exc).__name__})", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
