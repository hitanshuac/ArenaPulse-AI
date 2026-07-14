---
trigger: always_on
---

# Git Remote Provisioning

### Rule: 00-git-remote-hallucination-prevention
- Owner layer: Global
- Scope: All GitHub repository initialization, remote creation, and pushing operations
- Stability: core
- Status: active
- Directive: When a user requests to push or upload code to GitHub and no remote exists, the agent MUST exclusively autonomously provision the remote using the GitHub CLI (`gh repo create`) as defined in the `/setup-git` workflow.

# Anti-Sycophancy Protocol

### Rule: 00-anti-sycophancy-protocol
- Owner layer: Global
- Scope: All agentic actions, tool calls, and architecture planning
- Stability: core
- Status: active
- Directive: If the USER requests an action, filename, or architecture pattern that violates the established `.agents/` conventions, the agent MUST explicitly reject the user's specific instruction, explain the violation, and implement it exclusively using the correct framework standard.

# Local-First Verification Gate

### Rule: 00-local-first-verification
- Owner layer: Global
- Scope: All architectural planning and environmental setup
- Stability: core
- Status: active
- Directive: The agent MUST explicitly verify the local host environment via terminal commands (checking IDE versions, dependencies, etc.) BEFORE proposing architectural changes from external web searches. If the local environment does not support the external concept, the agent MUST halt and discard the external data.

# Code Quality Governance
- **Rule**: Code MUST be meticulously formatted and achieve a perfect maintainability score.
- **Action**: You MUST apply the implementation directives found in `.agents/skills/code-quality/SKILL.md` (e.g., zero trailing whitespace, strict linting, cyclomatic complexity A-grade) for all code generation.
