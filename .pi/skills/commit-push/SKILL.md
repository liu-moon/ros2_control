---
name: commit-push
description: Review workspace changes, create a clear Git commit, and push it to the configured remote. Use when the user asks to commit and/or push code changes.
---

# Commit and Push

Use this workflow from the repository root.

## Safety rules

- Never use `git add -A` or `git add .` without first reviewing what will be staged.
- Never commit secrets, credentials, tokens, generated build output, or unrelated files.
- Never use `--force`, `--force-with-lease`, or rewrite history unless the user explicitly requests it.
- Do not skip hooks or tests unless the user explicitly requests it.
- If the requested scope, commit message, or target branch is unclear, ask before committing.
- Before the irreversible commit and push actions, summarize the files, commit message, branch, and remote, then ask for confirmation unless the user has explicitly authorized those exact actions in the current request.

## Workflow

1. Inspect the repository:

   ```bash
   git status --short
   git branch --show-current
   git remote -v
   git log -5 --oneline
   ```

2. Review changes before staging:

   ```bash
   git diff
   git diff --stat
   git ls-files --others --exclude-standard
   ```

   Inspect relevant untracked files individually. Check for secrets and unwanted generated files.

3. Run the project's appropriate tests or checks. For this ROS 2 workspace, normally use:

   ```bash
   colcon build --symlink-install
   ```

   If the Docker environment is required, run the equivalent command through the project's documented Docker workflow.

4. Stage only the intended files explicitly:

   ```bash
   git add path/to/file1 path/to/file2
   git diff --cached --stat
   git diff --cached
   ```

5. Create a concise imperative commit message, for example:

   ```bash
   git commit -m "Manage ROS repositories with vcstool"
   ```

6. Verify the commit and push target:

   ```bash
   git status --short
   git log -1 --oneline
   git branch -vv
   ```

7. Push the current branch using its configured upstream:

   ```bash
   git push
   ```

8. Report the commit hash, pushed branch, remote, and any checks that were run.

## Important repository detail

Repositories under `src/` managed by `vcstool` are external repositories and should not be staged in the parent repository. Only commit the parent workspace files, such as `repos.yaml`, `.gitignore`, README files, and local ROS packages.
