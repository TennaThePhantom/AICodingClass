
# REFLECTION.md

## 1. One problem the safety kit caught and one it missed

The safety kit caught a 75-character commit message during Task 1. When I tried to commit the safety kit with `git commit -m "feat(git): add safety kit with ship command, commit-msg and guard_git hooks"`, the `commit-msg` hook rejected it, because it was over the 72-character limit. it had to shorten it to `feat(git): add safety kit and git hooks`. So that proves the enforced layer actually works.

But the safety kit missed that the `.venv/` folder was being tracked in git. When claude ran tests, it changed hundreds of `.pyc` files inside `.venv/`, and since those files were already tracked from an earlier week the `/ship` command had to manually ignore them. Our `.gitignore` rules stop new `.pyc` files but they can't untrack files that are already in the index. We need a one-time `git rm --cached` to fix that.

## 2. Parallel worktrees cost and value

Running two features in parallel cost me a manual merge conflict in `routes/api.py`. Feature A added a `q` parameter to `list_tasks_route`, and Feature B added an `overdue` parameter to the same function. Git couldn't auto-merge them, so I had to open the file and combine the two branches myself.

But it was totally worth it for this pair of features. Because we used worktrees, Claude's context window didn't get confused between the two tasks. When Claude built the due-dates feature, it didn't accidentally break the search feature because the search code was in a completely different directory. The merge conflict took around 5 minutes to fix, but doing both features one after the other would have taken way longer.

## 3. What I would change before using this on my capstone

Before using this on my capstone project, I would add a `git rm --cached` cleanup step for any files that are already tracked but should be ignored like `.venv/` and `__pycache__/`. I would also change the team policy to require a PR and code review even for small features. Right now the safety kit lets me commit directly to a feature branch and merge it locally. On a team of four someone else should review the code, especially because Claude wrote most of it and could accidentally change something that you didn't want exactly change. Finally, I would add a hook that blocks commits if the `.venv` folder is in the staging/commit area.