---
name: Agentic Refactor (Architecture Decomposition)
description: A rigid, 5-phase chain-of-thought workflow for decomposing monolithic anti-patterns ("God Objects") into cleanly separated, layered architectures, utilizing dynamic AST discovery (tach) and deterministic rule enforcement (pytest-archon).
---

# Agentic Refactor Workflow

**Trigger:** Mandatory when refactoring legacy code, breaking down files exceeding 500 lines, resolving complex data flow entanglement, or enforcing High-Level/Low-Level Design (HLD/LLD) boundaries.
**Trigger Phrases:** "refactor this", "fix the data flow", "break down this monolith", "apply the agentic refactor workflow".

This workflow enforces the exact chain of thought used by Senior Principal Engineers (and high-functioning LLMs) to safely untangle monolithic architectures without breaking downstream dependencies.

## Phase 1: Toolchain Bootstrapping
Before attempting architectural changes, the agent MUST explicitly install the required deterministic architectural static analysis tools into the local environment (or verify they exist).
- `run_command`: `pip install tach pytest-archon`

## Phase 2: Dynamic Architecture Discovery (As-Is)
The agent MUST run dynamic static analysis to map the *living* dependency graph, rather than relying on static images or assumptions.
1. Run `tach report` (or equivalent `tach` command) to dynamically generate a text-based dependency map of the real codebase.
2. The agent MUST read this map to proactively identify cyclic dependencies, loop engineering flaws, and structural bottlenecks.
3. The agent must actively hunt for the following anti-patterns:
   - **God Objects**: Files acting as monolithic controllers that handle UI, business logic, and data persistence simultaneously.
   - **Implicit Data Busses**: Untyped global state, flat dictionaries, or session states used to pass data between detached functions.
   - **Side Effects**: Database writes, file I/O, or external API calls happening inside rendering loops or pure logic functions.
   - **Resource Churn**: Redundant network/database connections created and destroyed inside rapid execution loops.

*Deliverable:* The agent MUST generate a clear textual representation of the exact "As-Is" data flow to visualize the entanglement based on the `tach` output.

## Phase 3: Issue Identification & Severity Mapping (Rule Traceability)
The agent must list the identified architectural flaws explicitly and assign them severities based on Rule Traceability. Every identified flaw MUST cite the specific `.agents/rules/` file and Tier level it violates:
- 🔴 **High (Tier 0-1)**: Data integrity and security risks (e.g., side-effects in render loops, CWE-74).
- 🟡 **Medium (Tier 2)**: Correctness, performance bottlenecks, missing test coverage, or validation bypasses.
- 🟢 **Low (Tier 3-4)**: Compliance, pure maintainability, styling, or documentation issues.

## Phase 4: Layered Decomposition (To-Be)
The agent must formulate a new architecture adhering strictly to the **Separation of Concerns (SoC)**. The proposed architecture MUST explicitly define these layers (if applicable to the stack):
1. **State Management**: Typed, validated models (e.g., Pydantic) acting as the single source of truth.
2. **Domain/Business Logic**: Pure, deterministic functions that take inputs and return outputs with zero side effects.
3. **External Services**: API boundaries, LLM prompt logic, and external integrations isolated from core math.
4. **Presentation/UI**: Thin orchestrators, views, or chart factories containing zero business logic.
5. **Persistence**: Consolidated database or file I/O operations behind connection pools.

*Deliverable:* The agent MUST draft a precise, actionable execution plan marking specific file changes using the following tags:
- `[NEW] <filename>`: For new, extracted service modules.
- `[MODIFY] <filename>`: For files being stripped down to thin orchestrators.
- `[DELETE] <filename>`: For components entirely replaced by the new architecture.

> **Automatic Escalation (LLM Council):** If the architectural decomposition is highly ambiguous, the agent MUST automatically trigger `.agents/skills/llm-council/SKILL.md` to resolve the ambiguity before proceeding.

## Phase 5: Verification & Safety Gates
Before executing the plan, the agent MUST:
1. **Deterministic Decoupling Check**: Before proposing any `[DELETE]` action for replaced modules, the agent MUST execute programmatic `grep_search` operations to mathematically prove zero downstream dependencies exist in the new codebase.
2. **HLD/LLD Rule Enforcement**: The agent MUST write `pytest-archon` test fixtures (e.g., `archon.architecture.rule("domain").should_not_import("routers")`) to mathematically lock in the new High-Level and Low-Level Design boundaries.
3. Generate an `implementation_plan.md` artifact incorporating Phases 2-5.
4. Explicitly ask for human approval before proceeding.

**Post-Execution Import Gate**: After refactoring, the agent MUST run programmatic import/build assertions and the `pytest-archon` test suite to prove the application dependency graph complies with the new architecture.

**Execution begins ONLY after user approval.**
