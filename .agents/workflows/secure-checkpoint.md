---
description: Automatically commit and push the current workspace state to GitHub to prevent data loss.
---

# Secure Checkpoint Workflow

1. Ask the user for a brief commit message describing the current state.
2. Stage all changes, commit with a conventional commit message, and push to the remote origin: // turbo
   - `git add .`
   - `git commit -m "[User Message]"`
   - `git push`
3. If the host project includes a custom Git management script (e.g., `src/capabilities/git_manager.py`), use that instead of raw git commands.
4. Confirm to the user that their files are permanently secured on GitHub.
