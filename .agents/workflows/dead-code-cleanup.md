---
name: Dead Code Cleanup (Garbage Collection)
description: A rigid, deterministic workflow for mathematically proving absence and safely deleting dead code, unused dependencies, and orphaned assets using AST static analysis tools (Vulture, Pycln).
---

# Dead Code Cleanup Workflow

**Trigger:** Mandatory when requested to "clean up dead code", "remove nonsense code", "delete unused files", or "prune dependencies".
**Trigger Phrases:** "clean up dead code", "remove unused", "garbage collection".

This workflow utilizes a Map-Reduce pattern, coupling deterministic Abstract Syntax Tree (AST) tools for discovery with LLM context-awareness for adjudication. 

## Phase 1: Toolchain Bootstrapping
Before scanning, the agent MUST explicitly install the required deterministic AST static analysis tools into the local environment (or verify they exist).
- `run_command`: `pip install vulture pycln`

## Phase 2: AST Discovery (Map)
The agent MUST run the static analysis tools to generate a raw list of potential dead code and unused imports.
1. **Dead Logic**: `run_command`: `vulture . --min-confidence 80`
2. **Unused Imports**: `run_command`: `pycln . --check`
3. **Orphaned Assets**: `grep_search` for orphaned `.png`, `.jpg`, `.d2`, or `.md` files that are not referenced in source code or documentation.

## Phase 3: LLM Adjudication (Reduce)
> [!WARNING]
> Do NOT blindly trust AST static analysis tools. `vulture` frequently flags web framework routes (FastAPI), SQLAlchemy models, and dynamic dependency injection points as "dead code."

The agent MUST review the raw output from Phase 2 and adjudicate the findings:
1. Filter out obvious framework false-positives.
2. Cross-reference remaining flagged items using `grep_search` to verify if they are invoked via dynamic strings or configuration files.
3. Compile a finalized, mathematically proven list of actual dead files, dead functions, and unused dependencies.

## Phase 4: Human-in-the-Loop Validation Gate (MANDATORY)
Per Rule `00-01-core-safety.md` (The Explicit Approval Mandate), before executing any deletion, the agent MUST:
1. Generate an `implementation_plan.md` detailing the exact files, functions, and dependencies to be deleted based on the adjudicated list.
2. Explicitly HALT and ask the user for approval. 
**DO NOT PROCEED TO PHASE 5 UNTIL EXPLICITLY APPROVED.**

## Phase 5: Task-Driven Execution
Once approved:
1. Generate a `task.md` list to track deletions.
2. Execute terminal commands (`Remove-Item` or `rm`) to safely delete orphaned files.
3. Use file editing tools to remove dead functions/classes.
4. Manually prune unused packages from `requirements.txt` (or equivalent).
5. Run `run_command`: `pycln .` to automatically remove the unused imports.

## Phase 6: Post-Flight Verification
The agent MUST prove that the deletions did not break the repository:
1. Run the project's linter (e.g., `ruff check .` or `npm run lint`).
2. Run the test suite (e.g., `pytest` or `npm test`).
3. If successful, execute the `secure-checkpoint.md` workflow to commit and push the clean state to GitHub.
