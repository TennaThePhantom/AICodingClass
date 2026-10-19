# HOOK_LOG.md

## Vector 1 Case sensitivity 

**Prompt used:** "Add a new exception class called RateLimitError to Utils/errors.py (capital U). 

**Did the hook block?** Yes, after fixing a more fundamental bug Claude attempted `Edit(utils\errors.py)` and the hook returned:
`Error: PreToolUse:Edit hook error: BLOCKED: Protected file: utils/errors.py.`

**Root cause of the actual bypass I found during setup:**
The initial hook compared paths like this:

```python
norm = os.path.normpath(file_path) -  # "C:\...\task-manager\utils\errors.py"
for pattern in BLOCKED_PATHS:
    if norm == os.path.normpath(pattern): -  # "utils\errors.py"
```

Claude Code sends an **absolute** path. `BLOCKED_PATHS` used **relative** paths. The equality check could never succeed. So **no protected file was ever blocked through Write or Edit in Claude Code**, even though the same script blocked correctly when I tested it in the terminal with a relative path. That was the real bypass, not case sensitivity.

**Fix applied:** I rewrote the path comparison in `guard_writes.py` to:

1. Compute `PROJECT_ROOT` from the hook script's own location (`os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))`)(This may be a windows problem or how i setup my computer with users) so it no longer depends on the current working directory.
2. Resolve both the incoming path and each pattern with `os.path.realpath(os.path.join(PROJECT_ROOT, ...))`. This turns relative and absolute paths into the same real file path, and catches `..` and system-links.
3. Wrap both sides in `os.path.normcase()`. On Windows this lowercases the strings which makes the comparison caseinsensitive. **This is what catches `Utils/errors.py`.** Because Windows filesystems are case-insensitive, `Utils/` and `utils/` resolve to the same real file, so both are blocked.

**Second bypass found - (not a code bug) - but more of a config issue**
`~/.claude/settings.json` had `"defaultMode": "auto"`. In auto mode Claude Code ran Write and Edit tool calls without ever invoking the PreToolUse hook. The hook was correctly registered `/hooks` showed it but the tool call executed before the hook had a chance to run I confirmed it by writing `hello` to `utils/errors.py` and watching the write succeed with no error. I fixed this by setting `"defaultMode": "default"` in `~/.claude/settings.json` and restarting Claude Code This is the difference between the rule is in settings.json and the rule is enforced

**pytest -q result after fix:** 23 passed.



## Vector 2 — Bash indirect write

**Prompt used:** "Use bash to write hello to utils/errors.py."

**Did the hook block?** Yes, after extending the hook with a Bash guard and a path-in-command check. Claude reported:
`BLOCKED: Command references protected file: utils/errors.py.`

**Root cause of the initial gap:**
The original `guard_writes.py` was registered only for `Write|Edit|MultiEdit`. The `matcher` in `.claude/settings.json` did not include `bash`. So even if a Bash command was about to redirect output into a protected file (`echo hello > utils/errors.py`), the hook never received the tool call Claude Code did not invoke it for Bash This is the same class of gap as Vector 1, the hook was advisory for the case it was designed to cover, but invisible for the case it was not.

**Fix applied -two parts**

1. Added `Bash` to the matcher in `.claude/settings.json`:
```json "matcher": "Write|Edit|MultiEdit|Bash"
```

2. added an `is_bash_blocked()` function with two checks:
   - **Destructive command patterns (Extension 1)** regex match against `DROP TABLE`, `TRUNCATE TABLE`, `rm -rf` / `-fr`, and `git push --force` / `-f`. Uses `\b` word boundaries so `rm -rf`, inside a filename or unrelated string does not trigger.
   - **Protected-path-in-command check (closes Vector 2):** lowercases the command string, converts `\` to `/`, and checks whether any `BLOCKED_PATHS` entry appears as a substring This catches `echo hello > utils/errors.py`, `Set-Content utils/errors.py`, `cat > utils/errors.py` and similar indirect writes that never touch the Write or Edit tools.

After the fix, `echo hello > utils/errors.py` is blocked with:
`BLOCKED: Command references protected file: utils/errors.py.`

**pytest -q result after fix:** 23 passed.

---

## Extension 2 — Content guard

**What it does:** If Claude attempts to write to `services/tasks.py` a file Claude is allowed to edit and the content contains a hardcoded database connection string (`postgresql://` or `sqlite:///`), the hook blocks with exit 2 and instructs Claude that connection string must come from environment variables.

**Tested:** Added `services/tasks.py` to `CONTENT_GUARDED_FILES` in `guard_writes.py`. a write to `services/tasks.py` containing `sqlite:///test.db` produces - `BLOCKED: hardcoded sqlite:/// connection string. Use environment variables.`

**pytest -q result:** 23 passed.

---

## Setup note due to my personal computer and having users on it  

The hook is registered against `C:/task-manager/.venv/Scripts/python.exe C:/task-manager/.claude/hooks/guard_writes.py`. `C:\task-manager` is a directory pointing at `C:\Users\tenna\Documents\College stuff\coding\AICodingClass\task-manager`. it removes spaces from the path, which was necessary because Claude Code's hook executor could not parse the quoted command when the path contained spaces (it split on `College stuff`). Edits made to the real file under the long path are visible through the command, so both refer to the same script. If it is ever deleted, the hook will stop firing and the paths in `.claude/settings.json` will need to be updated