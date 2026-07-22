---
name: Dead Code Cleanup (Garbage Collection & Semantic Pruning)
description: A rigid, deterministic workflow for mathematically proving absence of dead code using AST static analysis tools (Vulture, Pycln), combined with a semantic pruning phase to eliminate architectural "Scope Creep".
---

# Dead Code Cleanup & Semantic Pruning Workflow

**Trigger:** Mandatory when requested to "clean up dead code", "remove nonsense code", "delete unused files", "prune dependencies", or "remove scope creep".

This workflow utilizes a Map-Reduce pattern, coupling deterministic Abstract Syntax Tree (AST) tools for discovery of orphaned variables with LLM context-awareness to semantically prune out-of-scope code.

## Phase 1: Domain Alignment (Semantic Pruning)
Before looking for literal dead code, the agent MUST explicitly verify the codebase against its core domain to find "Scope Creep."
1. Read the `HANDOVER.md` and `docs/05_TICKETS.md` (if they exist) to establish the project's rigid boundaries (e.g. "This is a Stadium Cockpit, NOT a generic Chatbot").
2. `grep_search` for files, classes, or directories that violate these boundaries (e.g. `examples/` directories containing generic AI code, or open-ended rules that lack strict Pydantic validation).
3. Compile a list of active but out-of-scope files that must be pruned to restore architectural integrity.

## Phase 2: Toolchain Bootstrapping
The agent MUST explicitly install the required deterministic AST static analysis tools into the local environment (or verify they exist).
- `run_command`: `pip install vulture pycln`

## Phase 3: AST Discovery (Map)
The agent MUST run the static analysis tools to generate a raw list of potential dead code and unused imports.
1. **Dead Logic**: `run_command`: `vulture . --min-confidence 80`
2. **Unused Imports**: `run_command`: `pycln . --check`
3. **Orphaned Assets**: `grep_search` for orphaned `.png`, `.jpg`, `.d2`, or `.md` files that are not referenced in source code or documentation.

## Phase 4: LLM Adjudication (Reduce)
> [!WARNING]
> Do NOT blindly trust AST static analysis tools. `vulture` frequently flags web framework routes (FastAPI), SQLAlchemy models, and dynamic dependency injection points as "dead code."

The agent MUST review the raw output from Phase 3 and adjudicate the findings:
1. Filter out obvious framework false-positives.
2. Cross-reference remaining flagged items to verify if they are invoked via dynamic strings or configuration files.
3. Combine the mathematically proven list of dead files/functions with the list of out-of-scope files identified in Phase 1.

## Phase 5: Human-in-the-Loop Validation Gate (MANDATORY)
Per Rule `00-01-core-safety.md` (The Explicit Approval Mandate), before executing any deletion, the agent MUST:
1. Generate an `implementation_plan.md` detailing the exact files, functions, and dependencies to be deleted based on both semantic pruning and AST analysis.
2. Explicitly HALT and ask the user for approval. 
**DO NOT PROCEED TO PHASE 6 UNTIL EXPLICITLY APPROVED.**

## Phase 6: Task-Driven Execution
Once approved:
1. Generate a `task.md` list to track deletions.
2. Execute terminal commands (`Remove-Item` or `rm`) to safely delete orphaned and out-of-scope files.
3. Use file editing tools to remove dead functions/classes.
4. Run `run_command`: `pycln .` to automatically remove the unused imports.

## Phase 7: Post-Flight Verification
The agent MUST prove that the deletions did not break the repository:
1. Run the project's linter (e.g., `ruff check .` or `npm run lint`).
2. Run the test suite (e.g., `pytest` or `npm test`).
3. If successful, explicitly instruct the user to trigger the `secure-checkpoint.md` workflow to commit and push the clean state to GitHub.
