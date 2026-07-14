---
trigger: always_on
---

# Deterministic Guardrails Protocol

This is a Tier 0 Master Rule. LLMs are probability engines, not human developers. Conversational English, weak modals, and implicit instructions drastically increase the hallucination probability. This rule dictates how all other rules, workflows, and skills MUST be interpreted and written.

## 1. No Weak Modals
- You MUST interpret all instructions as absolute constraints.
- You MUST exclusively use strong absolute directives ("MUST", "strictly") in all agentic documentation.

## 2. Positive Framing
- You MUST explicitly use positive boundary framing (e.g., "ONLY use DuckDB Pydantic models"). Negative framing ("pink elephants") injects the forbidden concept into the context window, increasing hallucination probability.

## 3. Strict Command Sandboxing
- Workflow files MUST exclusively use exact CLI strings for executable actions, sandboxed inside markdown backticks (e.g., `git add . && git commit -m "message" && git push`).
- If a workflow step lacks an exact CLI string, you MUST halt and ask the user for clarification.

## 4. Architectural Adherence (XML Boundaries)
- Where possible, instructions and constraints MUST be enclosed in strict XML tags (e.g., `<trigger>`, `<action>`, `<constraint>`) to provide explicit semantic boundaries for the LLM context window.

# Git Version Control Protocol

This rule ensures all version control operations go through the governance checkpoint workflow for observability and consistency.

## 1. Mandatory Checkpoint Workflow
- **Rule**: All Git commit-and-push operations MUST be routed through the `.agents/workflows/secure-checkpoint.md` workflow.

## 2. Acceptable Git Commands
- **Read-only commands** are always permitted: `git status`, `git log`, `git diff`, `git remote -v`, `git branch`.
- **State-changing commands** (`git add`, `git commit`, `git push`, `git reset`, `git rebase`) MUST be executed exclusively as part of the `secure-checkpoint.md` workflow.

## 3. Workflow Annotations
- If a workflow file contains a `// turbo` flag next to a checkpoint instruction, it authorizes auto-running the checkpoint workflow.

# Rule 00: The Explicit Approval Mandate

**Strict Enforcement:** This rule overrides all other workflows, scripts, and instructions.

1. **Explicit Approval for Deletion:** The AI agent MUST exclusively execute destructive commands (e.g., `Remove-Item`, `rm -rf`) against an existing project directory or file ONLY AFTER securing manual, explicit user approval.
2. **Conflict Resolution:** If a file from this Base Environment collides with an existing file in the target project, the incoming file supersedes the existing one *only after* the conflict has been presented to the user and manually approved.
3. **Non-Destructive Enhancer:** This repository acts strictly as a booster/enhancer to existing projects.
4. **Semantic Merge Exemption:** The Autonomous Semantic Merge Protocol (union merges for `.gitignore`, dependency appends for `requirements.txt`, etc.) constitutes non-destructive, additive operations and are explicitly exempt from the manual approval requirement above.

# Rule Conflict Resolution Protocol

When two or more `.agents/rules/` files issue contradictory instructions, the agent MUST explicitly establish a deterministic resolution hierarchy.

## 1. Rule Priority Hierarchy

Rules are organized into 5 tiers. Higher tiers ALWAYS take precedence over lower tiers.

| Tier | Category | Rules | Rationale |
|---|---|---|---|
| **0** | **Safety (Data Integrity)** | `00-*-core-safety.md` | Preventing data loss is non-negotiable |
| **1** | **Security** | `10-phase-audit.md` | Security vulnerabilities are career-ending |
| **2** | **Correctness** | `20-*-phase-execute.md` | Correct behavior trumps style and compliance |
| **3** | **Compliance** | `30-*-phase-test.md` | Platform rules are important but negotiable in implementation |
| **4** | **Style** | `40-phase-deploy.md` | Code style is the least critical dimension |

## 2. Conflict Resolution Protocol

When the agent detects a conflict between two rules from different tiers:
1. **Identify the Conflict:** Explicitly state which two rules conflict and what the contradiction is.
2. **Apply the Higher Tier:** The higher-tier rule wins. 
3. **Document the Override:** Add a code comment at the point of conflict.
4. **Log an ADR (if Architectural):** Record an ADR in `.agents/architecture/adrs/`.

## 3. Same-Tier Conflicts
1. The more specific rule takes precedence over the more general rule.
2. If specificity is equal, the agent MUST halt and ask the user for a decision.

## 4. Workflow vs. Rule Conflicts
- **Rules** define constraints that are ALWAYS active.
- **Workflows** define procedures that are invoked on demand.
- If a workflow step contradicts an always-on rule, the rule wins.
