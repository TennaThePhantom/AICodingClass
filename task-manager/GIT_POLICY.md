# Team Git Policy - Task Manager

This policy is for a four-person team working on the task-manager project with Claude Code.

## Branch Naming and Commits
* **Branch naming:** `feat/<scope>-<desc>`, `fix/<scope>-<desc>`, or `chore/<desc>` (e.g., `feat/tasks-keyword-search`).
  * **Mechanism:** Advisory in `CLAUDE.md`.
* **Commit format:** `type(scope): subject` or `type: subject`. Types allowed: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`, `perf`. Subject lowercase, imperative, max 72 chars.
  * **Mechanism:** Enforced by the `.githooks/commit-msg` hook (rejects bad commits) and the `/ship` command (proposes valid messages).

## Attribution
* **Decision:** Drop the `Co-Authored-By: Claude` trailer. 
* **Why:** The human is responsible for the code, and the safety kit/hook logs provide a better audit trail than a git trailer.
* **Mechanism:** Do not include it in `/ship` templates. Human review rejects PRs that add it.

## Parallel Worktrees vs. Sequential
* **Use Parallel Worktrees:** When two features do not share files, or when two team members are building separate features. 
* **Use Sequential:** When changing core files (like `services/tasks.py` or `routes/api.py`), unless the features are truly independent (like our search and due-date features). Both features must be merged locally and pass `pytest -q` before pushing.
  * **Mechanism:** Advisory in `CLAUDE.md`. The `/ship` command prevents committing until tests pass.

## Review and Merge Rules
* **Human Reviewer Required:** Any PR that resolves a git conflict, changes a test, or alters the database schema.
* **No Weakened Tests:** Reviewers must reject PRs that change `pytest.raises(ValidationError)` to `pytest.raises(Exception)`.
* **No Pushing to Main:** All commits must go to a feature branch and merge via PR.
  * **Mechanism:** Enforced by `.claude/hooks/guard_git.py` (blocks `git push origin main`) and human review.

## Forbidden Commands
* **No Force Pushes:** Never use `--force`, `-f`, or `--force-with-lease`.
* **No Skipping Hooks:** Never use `--no-verify` or `-n`.
  * **Mechanism:** Enforced by `.claude/hooks/guard_git.py` for Claude Code sessions. Human terminal usage is governed by team trust and branch protection rules on GitHub.