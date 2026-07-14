# Project Context

## Purpose

Antigravity is a portable, evidence-grounded repository knowledge engine. Its
primary workflow is:

- `ag-refresh` scans a workspace and builds `.antigravity/` knowledge artifacts.
- `ag-ask` routes codebase questions to the relevant module context and answers
  with source evidence.
- Native plugins, raw CLI entrypoints, context files, and `ag-mcp` expose the
  same knowledge layer to different AI development environments.

Secondary features such as project bootstrapping, tools, MCP consumption, memory,
and sandbox execution should support that repository knowledge layer rather than
turn the repo into a generic agent platform.

## Tech Stack

- **Language:** Python 3.10+
- **LLM providers:** OpenAI-compatible endpoints by default, Gemini supported
  through `GOOGLE_API_KEY` / `GEMINI_MODEL_NAME`.
- **Data Validation:** Pydantic for settings, contracts, and structured payloads.
- **Knowledge Hub:** `openai-agents[litellm]` for multi-agent refresh and ask
  pipelines.
- **Integration:** Model Context Protocol (MCP) for optional server and consumer
  flows.
- **CLI:** `typer` + `rich` for `ag` and engine entrypoints.
- **Testing:** Pytest.
- **Environment:** `python-dotenv` / pydantic-settings for configuration.

## Project Conventions

### Code Style

- Type hints are expected for public functions.
- Tool functions should have clear docstrings so agent-facing discovery remains
  understandable.
- Use Pydantic models for complex structured data.
- Prefer explicit, small modules over implicit magic.

### Architecture Patterns

- The core product boundary is the knowledge workflow: refresh, ask, and the
  `.antigravity/` artifacts they produce.
- Local tools and MCP tools should be explicit delivery surfaces with documented
  permissions.
- Generated state belongs under `.antigravity/`, `memory/`, or `artifacts/` as
  appropriate; do not hide persistent behavior in unrelated paths.
- `ag init` / `agent-repo-init` is for scaffolding new repositories; it is not
  required before `ag-refresh` on an existing repository.

### Testing Strategy

- Use `pytest` for engine and CLI tests.
- Add focused tests for user-visible contracts, safety boundaries, and docs drift.
- Run `python scripts/check_repo_contract.py` after changing product metadata,
  installation flows, or docs.

### Git Workflow

- Standard feature-branch workflow.
- Commits should be atomic and descriptive.
- Documentation should be updated with code changes that alter public behavior.

## Knowledge Hub

- **Hub module** (`engine/antigravity_engine/hub/`): scans the workspace,
  generates conventions and module knowledge, builds routing indexes, and answers
  project questions via LLM.
- **CLI commands:** `ag-refresh` builds or refreshes `.antigravity/`; `ag-ask`
  answers grounded project questions; `ag-mcp` exposes `ask_project` and
  `refresh_project` to MCP hosts. The wrapper `ag refresh` / `ag ask` commands
  are also available when both CLI and engine packages are installed.

## Security Boundaries

- The default local sandbox is for trusted local workspaces, not untrusted-code
  isolation.
- If opt-in sandbox runtimes are unavailable, the engine warns before falling
  back to local execution.
- `AG_RETRIEVAL_MODE=compact` is the default. `full` keeps richer artifacts;
  common secrets are redacted before write, but source snippets can still be
  captured.
- External MCP server consumption requires explicit opt-in via `MCP_ENABLED=true`
  and `AG_ALLOW_MCP=true`. Stdio MCP servers inherit the process environment plus
  configured `env` values.

## External Dependencies

- **LLM endpoint:** OpenAI-compatible endpoint or Gemini provider credentials.
- **MCP servers:** Optional external servers, enabled only when trusted.
- **Microsandbox:** Optional runtime for stronger code execution isolation than
  the local subprocess fallback.
