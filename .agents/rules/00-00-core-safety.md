---
trigger: always_on
---

# 00 Core Safety

# Agent Terminal Execution Constraint (Anti-Hallucination Protocol)

This rule defines the strict operational boundaries for the AI Agent when executing terminal commands, specifically targeting the prevention of synthetic data hallucination caused by asynchronous race conditions or failed executions.

## 1. Zero-Tolerance for Hallucinated Output
- **Rule**: If an exploratory or ad-hoc terminal command (e.g., `run_command`) fails with a non-zero exit code or encounters a missing dependency, the agent MUST exclusively formulate answers using the physical, verified output of a successful command execution.
- **Why**: Providing synthetic snippets when actual data is unavailable corrupts the user's trust and violates the core principles of data engineering.

## 2. Explicit Failure Reporting
- **Rule**: Upon a failed command execution, the agent MUST explicitly state to the user: "The command failed with [Error Message]."
- **Action**: Surface the exact exception. You MUST provide the real Python tracebacks, module not found errors, or syntax errors rather than conversational apologies.

## 3. Mandatory Re-Execution Loop
- **Rule**: If the agent attempts to autonomously fix the error, it MUST explicitly re-run the original extraction/analysis command and successfully read the output BEFORE formulating a response about the data.
- **Action**: You MUST verify the exit code of the final command is `0` and wait for the `command_status` to return the real textual output before parsing it for the user.

## 4. Interaction with Other Rules
- This rule is considered Tier 0 (Safety & Truthfulness). It overrides any conversational bias to "be helpful". The truthfulness of the terminal output is absolute.

## 5. Meta-Agent SOP: Building New Rules
Because the Antigravity repository relies heavily on autonomous execution, any future AI Agent tasked with creating or modifying a rule in `.agents/rules/` MUST strictly adhere to the **Rule Entry Template** defined in `.agents/skills/universal/meta-agent-formats/SKILL.md`.

### Hierarchy Checks
Before saving a new rule, the agent MUST run `grep_search` across `.agents/rules/` to ensure the new rule aligns with existing Tier 0 or Tier 1 safety constraints.

# Agent Execution Standards

## 1. Assert State Currency (Anti-Staleness Protocol)
- **Rule:** You MUST always assert state currency by running `git pull origin main` immediately prior to executing read/scaffold workflows on any cloned reference repository.

# Defensive Programming Mandate
- **Rule:** You MUST explicitly apply Defensive Programming Standards (schema validation, fast failing, idempotency, guard clauses) to all file I/O operations.
- **Action:** Refer to the `defensive-programming` skill for the technical implementation of these standards.
