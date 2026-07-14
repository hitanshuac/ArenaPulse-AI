---
name: Local Bootstrapper
description: Workflow to scaffold and verify the local environment before execution.
---

# Bootstrap Workflow

This workflow has two modes of operation:
- **First Run:** Scaffolds the Antigravity Environment from scratch in a new or existing repository.
- **Upgrade Run:** Detects an older installed version and safely merges the latest Antigravity assets without destroying host project code.

Execute the phases sequentially. Phase 0 is only relevant for repositories that have already been bootstrapped once.

> **CRITICAL AUDIT RULE**: During verification phases (1-8), the agent is in **read-only audit mode** per `00-01-core-safety.md` (Audit Integrity rule). The agent MUST NOT create, modify, or delete project files to make an audit pass. If a required item is missing, report it as `[FATAL]` or `[SKIPPED]` and continue to the next phase. Present a consolidated report at the end.

---

## Phase 0: Environment Upgrade Protocol (Existing Repositories Only)

**Skip this phase if this is the first time running bootstrap in this repository.**

1. **Detect Existing Installation:** Check if `.agents/workflows/` already exists. If it does, this is an upgrade run.
2. **Clone Latest Upstream:** // turbo
   - Run `git clone https://github.com/hitanshuac/antigravity-agentic-governance-template.git .agents/tmp/antigravity_latest`
3. **Verify Semantic Release Context:** Confirm that `.agents/tmp/antigravity_latest/.agents/workflows/semantic-release.md` exists. This anchors the version context for the upgrade.
4. **Interactive Upgrade & Cleanup:**
   - Compare `.agents/tmp/antigravity_latest/.agents/` against the local `.agents/` directory.
   - Copy all entirely *new* files (workflows, rules, skills, product templates) into the local `.agents/` folder.
   - **Deprecated Files:** Identify files that exist locally but NOT in the upstream template (i.e., old rules or workflows). **DO NOT delete them automatically.** Present a list of these old files to the user and request **manual confirmation**. Only delete them once explicit approval is given.
   - **Do NOT overwrite** any existing files that the host project has already modified without asking first.
5. **Union Merge Boilerplate:** Execute `.agents/workflows/merge-conflict-resolution.md` to safely union-merge `.gitignore` and any dependency manifests.
6. **Cleanup:** Delete `.agents/tmp/` entirely, then proceed to Phase 1.


---

## Phase 1: Verify Governance Integrity

1. Confirm the `.agents/` folder is intact and contains `workflows/`, `rules/`, and `product/templates/`.
2. If the host project contains source code directories (e.g., `src/`, `app/`, `lib/`), verify they are structurally sound. If this is a pure governance template with no application code, mark this check as `[SKIPPED - governance template]`.

## Phase 2: Verify Dependencies

1. **Detect the host project's dependency manifest** by scanning for: `requirements.txt` (Python), `package.json` (Node.js), `go.mod` (Go), `Cargo.toml` (Rust), `pom.xml` (Java), or equivalent.
2. If a manifest exists, verify dependencies are pinned (exact versions or range-locked). Install them using the appropriate package manager (e.g., `pip install -r requirements.txt`, `npm install`, `go mod download`). // turbo
3. If a virtual environment or equivalent isolation mechanism is used (e.g., `.venv/`, `node_modules/`), confirm it is excluded by `.gitignore`.
4. If no dependency manifest exists (pure governance template), mark this phase as `[SKIPPED - no dependencies]`.

## Phase 3: Verify Config & Secrets

1. Check if `.secrets` or `.env` exists. If not, generate a placeholder.
2. Run a search for leaked API keys inside the project's source directories. If any are found, immediately purge them and move them to `.secrets`.
3. Ensure `.gitignore` is active and blocking `.secrets/`, `.env`, and `data/`.
4. **Remote CI/CD Alignment:** Execute `.agents/workflows/setup-secrets.md` to ensure the upstream GitHub repository is provisioned with any required Action secrets.

## Phase 4: Verify Product Design Gate

1. Confirm that `.agents/product/templates/` exists and contains all 5 templates (`01_PRD.md`, `02_TAD.md`, `03_SECURITY.md`, `04_FRONTEND.md`, `05_TICKETS.md`).
2. If the user is building a new project, execute `.agents/workflows/generate-product-docs.md` to populate them before allowing any code generation.

## Phase 5: Verify Observability

1. Ensure the `data/` directory exists (with `.gitkeep`).
2. Confirm `data/error_logs.json` exists or can be initialized by the `error-observability.md` workflow.

## Phase 6: Verify Local Enforcement (Pre-commit & Linting)

1. Confirm `.pre-commit-config.yaml` exists at the repo root. If not, mark as `[SKIPPED - no pre-commit config]`.
2. If it exists, run `pre-commit install` to ensure hooks are active. // turbo
3. **Detect the host project's linter** by scanning for config files (e.g., `ruff.toml` for Python, `.eslintrc` for JS/TS, `golangci-lint.yml` for Go). Run the appropriate linter. If no linter config exists, mark as `[SKIPPED - no linter configured]`. // turbo

## Phase 7: Verify Testing Infrastructure

1. **Detect the host project's test framework** by scanning for test directories (`tests/`, `src/tests/`, `__tests__/`, `*_test.go`) and test runner configs (`pytest.ini`, `jest.config.*`, etc.).
2. If tests exist, run them using the detected framework (e.g., `pytest -v`, `npm test`, `go test ./...`). // turbo
3. If tests fail, execute `.agents/workflows/error-observability.md` to log and diagnose the failures.
4. If no test infrastructure exists (pure governance template), mark as `[SKIPPED - no test suite]`.

## Phase 8: Verify Automation Capabilities

1. If the host project includes automation scripts or CI/CD integration files (e.g., `.github/workflows/`, custom CLI tools), verify they are intact.
2. Confirm the GitHub CLI (`gh`) is installed and authenticated by running `gh auth status`. // turbo
3. If no automation capabilities exist (pure governance template), mark as `[SKIPPED - no automation scripts]`.

---

## Phase 9: Consolidated Report

Present a summary table of all phases with their status:

| Phase | Check | Status |
|---|---|---|

| 1 | Governance Integrity | `[PASSED]` / `[FATAL]` / `[SKIPPED]` |
| 2 | Dependencies | `[PASSED]` / `[FATAL]` / `[SKIPPED]` |
| 3 | Config & Secrets | `[PASSED]` / `[FATAL]` / `[SKIPPED]` |
| 4 | Product Design Gate | `[PASSED]` / `[FATAL]` / `[SKIPPED]` |
| 5 | Observability | `[PASSED]` / `[FATAL]` / `[SKIPPED]` |
| 6 | Linting & Pre-commit | `[PASSED]` / `[FATAL]` / `[SKIPPED]` |
| 7 | Testing Infrastructure | `[PASSED]` / `[FATAL]` / `[SKIPPED]` |
| 8 | Automation Capabilities | `[PASSED]` / `[FATAL]` / `[SKIPPED]` |

If any phase is `[FATAL]`, the bootstrap is NOT complete. Present the failures and await user instructions.
