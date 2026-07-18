---
name: Dead Code Cleanup (Garbage Collection)
description: A rigid, deterministic workflow for mathematically proving absence and safely deleting dead code, unused dependencies, and orphaned assets.
---

# Dead Code Cleanup Workflow

**Trigger:** Mandatory when requested to "clean up dead code", "remove nonsense code", "delete unused files", or "prune dependencies".
**Trigger Phrases:** "clean up dead code", "remove unused", "garbage collection".

This workflow encodes a "deterministic hierarchical linear scan" to ensure files are mathematically proven to be orphaned before proposing deletion. It MUST run separately from architectural refactoring workflows to prevent context window bloat.

## Phase 1: Global Workspace Reconnaissance (Broad to Narrow)
The agent MUST perform a read-only scan of the repository to understand its shape:
1. Scan the root directory.
2. Scan primary functional directories (e.g., `src/`, `tests/`, `docs/`).
3. Read configuration files that dictate behavior: `.gitignore`, `.semgrepignore`, `requirements.txt` (or equivalent package manager file).

## Phase 2: Reference Verification (Deterministic Proof of Absence)
Instead of guessing or assuming a file is dead, the agent MUST use programmatic `grep_search` operations to mathematically prove a file or dependency is unreferenced.
1. **Asset & File Verification**: Run `grep_search` across the entire codebase for the filenames or variable names suspected to be orphaned.
2. **Dependency Verification**: Run regex `grep_search` on imports across all source files to verify that dependencies listed in `requirements.txt` are actually imported.
3. **CI/Script Verification**: Verify if CI workflows or deployment scripts refer to tools or assets that no longer exist.

## Phase 3: Human-in-the-Loop Validation Gate (MANDATORY)
Per Rule `00-01-core-safety.md` (The Explicit Approval Mandate), before executing any deletion, the agent MUST:
1. Generate an `implementation_plan.md` detailing the exact files and dependencies to be deleted.
2. Explicitly HALT and ask the user for approval. 
**DO NOT PROCEED TO PHASE 4 UNTIL EXPLICITLY APPROVED.**

## Phase 4: Task-Driven Execution
Once approved:
1. Generate a `task.md` list to track deletions.
2. Execute terminal commands (e.g., `Remove-Item` or `rm`) to safely delete the orphaned files and empty directories.
3. Manually prune unused packages from `requirements.txt` (or equivalent).

## Phase 5: Post-Flight Verification
The agent MUST prove that the deletions did not break the repository:
1. Run the project's linter (e.g., `ruff check .` or `npm run lint`).
2. Run the test suite (e.g., `pytest` or `npm test`).
3. If successful, execute the `secure-checkpoint.md` workflow to commit and push the clean state to GitHub.
