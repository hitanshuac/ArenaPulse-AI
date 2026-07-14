---
trigger: glob
glob: "src/**/*.py"
---

# 20 Phase Execute

# OWASP LLM Security Standards (MLSecOps)

This is a Tier 1 Security Rule. AI agents and human developers are fundamentally unreliable at applying conversational security policies. Therefore, this repository enforces security via architectural physical barriers (The Interceptor Pattern).

## 1. The SecureLLMClient Exclusive Mandate
- **Rule**: You MUST exclusively import raw LLM provider SDKs (e.g., `openai`, `anthropic`, `google.generativeai`) inside the `src/security/` directory. 
- **Action**: For all application logic, UI, or API routing layers (e.g., `src/ui/` or `src/routers/`), you MUST exclusively route LLM interactions through the `SecureLLMClient` interceptor wrapper.

## 2. The Golden Wrapper Mandate
- **Rule**: All interactions with external Large Language Models MUST be routed through the `SecureLLMClient` interceptor class.

## 3. Bi-Directional Sanitization (Input & Output)
When modifying or extending the `SecureLLMClient`, you must enforce symmetry:
- **Pre-Flight (LLM01 Defense):** The wrapper must intercept the inbound payload and truncate it to a safe maximum length, strip raw HTML, and neutralize injection delimiters before sending it to the API.
- **Post-Flight (LLM06 Defense):** The wrapper must intercept the outbound response and scan it for Sensitive Information Disclosure before returning it to the caller.

## 4. CI/CD Preflight Gate
- Before concluding any task involving LLM integration, you MUST verify that all LLM calls route through `SecureLLMClient`. If a raw import is found outside of `src/security/`, you must immediately refactor it.

# 12-Factor App Enforcement

This rule mandates that all code deployed within the Agentic Environment strictly adheres to the 12-Factor App methodology.

## 1. Codebase
- One codebase tracked in revision control, many deploys.

## 2. Dependencies
- Explicitly declare and isolate dependencies (e.g., `requirements.txt`).

## 3. Config
- Store configuration in the environment. You MUST exclusively use `.env` locally or GitHub Secrets in CI/CD. Configuration MUST be injected dynamically.

## 4. Backing Services
- Treat backing services (databases, caches) as attached resources.

## 5. Build, Release, Run
- Strictly separate build and run stages.

## 6. Processes
- Execute the app statelessly. Stateful persistence MUST be delegated to backing services.

## 7. Port Binding
- Export services via port binding.

## 8. Concurrency
- Scale out via the process model.

## 9. Disposability
- Maximize robustness with fast startup and graceful shutdown.

## 10. Dev/Prod Parity
- Keep development, staging, and production as similar as possible.

## 11. Logs
- Treat logs as continuous event streams. Use lock-free background threadpools to push telemetry.
- If JSON logs are used as fallback, they MUST be append-only. 

## 12. Admin Processes
- Run admin/management tasks as isolated one-off processes in a dedicated `scripts/` directory.
