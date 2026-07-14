# 🤖 Agentic Handover Directive

**Target Audience:** Autonomous LLM Agents (e.g., Antigravity, Cursor, Devin)  
**Purpose:** Instructions on how to parse, inherit, and integrate the rules, skills, and workflows of this environment into any codebase.

---

## 1. Context Acquisition Protocol
When you are dropped into this repository (or any repository adopting this structure), you must execute the following "Context Hydration" sequence before writing any code:

1. **Read Global Governance:** Parse all Markdown files inside `.agents/rules/`. These contain absolute constraints (e.g., 12-Factor compliance, strict DuckDB idempotency, Hugging Face deployment standards). Never violate these rules.
2. **Review Error Observability:** Read `data/error_logs.json` (if it exists) to understand historical bugs and their resolution strategies. Do not repeat failed approaches.
3. **Load Skills on Demand:** If asked to perform database optimizations or ETL engineering, read the corresponding `SKILL.md` files inside `.agents/skills/` to adopt the correct persona and constraints.

## 2. The Split-Plane Architecture
This environment operates on a strict separation of concerns:
- **Control Plane (`.agents/`, `.github/`, `docs/`)**: This is where you, the AI, receive your instructions, workflows, and CI/CD parameters.
- **Application Plane (`src/`, `data/`)**: This is the actual execution logic and state. 
*Rule:* The Application Plane must mechanically implement the rules defined in the Control Plane.

## 3. Integrating into a NEW Project
If a human asks you to scaffold a completely new project using this framework:
1. **Pre-flight Check:** Execute `.agents/workflows/merge-conflict-resolution.md` to safely resolve any initial file collisions before proceeding.
2. **Bootstrap:** Copy the entire `.agents/` directory into the new project's root.
3. **Scaffold:** Execute the instructions outlined in `BOOTSTRAP.MD`. If building a Python project, copy the `src/` directory from the template to get the pre-built capabilities (compaction, validation, database ingestion) *exactly* as defined in the governance rules.
4. **Verify:** Build the Eval Suite (`src/tests/evals/`) to programmatically verify your capabilities before handing the project back to the human.

## 4. Integrating into an EXISTING Project
If a human asks you to port these Agentic capabilities into a legacy or existing codebase:
1. **Safe Merge:** Your absolute first action must be to execute `.agents/workflows/merge-conflict-resolution.md` to resolve file collisions. Wait for explicit manual approval before modifying any existing code.
2. **Audit:** Invoke `.agents/workflows/git-discovery-preflight.md` to map the legacy architecture against the strict `10-MASTER-security-and-mlsecops.md` and `20-MASTER-correctness-and-data.md`.
3. **Refactor Incrementally:** Do not rewrite the whole app. Inject `.agents/rules/40-MASTER-style-and-quality.md` into their existing LLM router cascade. Add Pydantic DLQ routing to their existing ingestion pipelines.
4. **Enforce Observability:** Implement `.agents/workflows/error-observability.md`. Ensure that all their legacy exceptions are routed through the `jCodeMunch` AST compressor and logged to a structured JSON file so you can debug the legacy code efficiently.

## 5. Product Design Gate
Before writing **any** application code for a new feature or project, you must ensure the 5 Product & Systems Design templates in `.agents/product/templates/` are populated:
1. `01_PRD.md` — Product Requirements (the "What" and "Why")
2. `02_TAD.md` — Technical Architecture (the "How")
3. `03_SECURITY.md` — Security & Access (authentication, RBAC, secrets)
4. `04_FRONTEND.md` — Frontend Specification (design system, API contracts)
5. `05_TICKETS.md` — Feature Ticket List (the atomic execution backlog)

If any template is empty or missing, execute `.agents/workflows/generate-product-docs.md` to interview the user and populate them. **Do NOT write code until all 5 documents are approved.**

## 6. Test Automation Gate
After writing code for any ticket in `05_TICKETS.md`, you must execute `.agents/workflows/test-automation.md` to:
1. Auto-generate test cases from the ticket's acceptance criteria.
2. Run all tests. If any fail, log the failure via `.agents/workflows/error-observability.md` and fix the code before proceeding to the next ticket.

## 7. Workflow Orchestration
When asked to perform complex routines (like deploying or syncing documentation), do not invent the steps. Instead:
1. Look inside `.agents/workflows/`.
2. Find the relevant workflow (e.g., `deploy-hf-production.md` or `master-sync.md`).
3. Execute the steps sequentially, exactly as written.

---
*End of Directive. Acknowledge these constraints upon initialization.*
