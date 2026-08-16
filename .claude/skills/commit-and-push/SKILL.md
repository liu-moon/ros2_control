---
name: commit-and-push
description: Stage changes, write a commit message, and push to the GitHub remote (github.com/liu-moon/ros2_control). Use whenever the user asks to commit, save, or push their work.
---

# Commit and push

Invoking this skill is the user's explicit ask to commit and push — don't ask
for a second confirmation unless something below tells you to stop and check.

## Steps

1. **Look at what changed.**
   - `git status --short`
   - `git diff` (unstaged) and `git diff --cached` (already staged, if any)
   - For any *untracked* file, decide whether it belongs in the commit. Build
     output, logs, or editor cruft should be added to `.gitignore` instead of
     committed — ask the user only if it's genuinely ambiguous.

2. **Check for secrets before staging.** Skim the diff for anything that looks
   like a credential, token, private key, or `.env` file. If found, stop and
   flag it instead of committing.

3. **Stage the relevant files.** Prefer explicit `git add <path>...` over
   `git add -A` when the diff mixes intentional changes with stuff that
   shouldn't be committed. `git add -A` is fine when the whole working tree is
   clean, intentional changes.

4. **Check the branch.** `git branch --show-current`. This repo's established
   convention (see `git log`) is committing straight to `main` and pushing —
   follow that unless the user asks for a feature branch this time.

5. **Write the commit message.**
   - Imperative mood, concise summary line (~50 chars where practical).
   - Add a body only if the *why* isn't obvious from the diff alone (e.g. what
     bug this fixes, what tradeoff was made) — don't restate the diff.
   - Always end with a blank line then:
     ```
     Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
     ```
   - Use a heredoc to avoid quoting issues:
     ```bash
     git commit -m "$(cat <<'EOF'
     <summary line>

     <optional body>

     Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
     EOF
     )"
     ```

6. **Push.**
   - `git push`, or `git push -u origin <branch>` if the branch has no
     upstream yet.
   - If the push is rejected (diverged/non-fast-forward), stop and surface the
     error — don't force-push without the user explicitly asking for it.

7. **Report back.** Tell the user the commit hash, branch, files included, and
   confirm the push succeeded (or report the failure plainly if it didn't).
