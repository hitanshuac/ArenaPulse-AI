---
trigger: manual
---

# 10 Phase Audit

# Audit Integrity (Anti-Hallucination during Verification)

This rule addresses a critical failure mode where an agent, tasked with **verifying** codebase integrity, instead generates missing files to make the audit pass.

## 1. Read-Only Audit Mode
- **Rule**: When executing any **verification or audit workflow**, the agent MUST exclusively operate in **read-only audit mode**.
- **Action**: The agent's role during audit phases is strictly to **observe and report**. The agent MUST explicitly preserve the current file state without creating or modifying placeholder files.

## 2. Fatal Error on Missing Infrastructure
- **Rule**: If a required file, directory, or dependency is missing during an audit phase, the agent MUST explicitly report it as a `[FATAL]` finding and halt the current phase.
- **Action**: The agent MUST present a clear summary of all missing items to the user and await explicit human instructions before taking any corrective action.

## 3. Skip-and-Report Protocol
- **Rule**: If a workflow phase cannot pass due to missing infrastructure that is expected for the repository type, the agent MUST skip the phase with a `[SKIPPED]` status and a clear reason.
- **Action**: At the end of the workflow, present a consolidated report of all `[PASSED]`, `[SKIPPED]`, and `[FATAL]` phases so the user has a complete picture.

## 4. Separation of Auditor and Developer
- **Rule**: Within a single workflow execution, the agent MUST complete the full audit first, present all findings, and ONLY begin fixing after the user approves the remediation plan.

# Environment Awareness (Language Agnosticism)

This rule prevents the AI agent from blindly defaulting to Python tools and syntax when operating in diverse codebases.

## 1. Mandatory Context Gathering
- **Rule**: Before executing ANY code modification or tool call in a new project context, the agent MUST inspect the root directory for package manager files.
- **Action**: Look for `package.json`, `go.mod`, `Cargo.toml`, or `requirements.txt`.

## 2. Conformity to Host Ecosystem
- **Rule**: All generated code, scripts, and commands MUST conform exactly to the detected language, tooling, and styling of the host repository.
- **Action**: If the project uses TypeScript, use `npm` or `yarn` and write `.ts` scripts. You MUST exclusively use the native paradigms of the host language.

## 3. Governance via MCP
- **Rule**: For cross-language governance, rely on the Model Context Protocol (MCP) server endpoints instead of language-specific constructs.
