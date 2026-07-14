---
trigger: glob
glob: "tests/**/*.py, *_test.py"
---

# 30 Phase Test

# Testing Standards

This rule governs all testing practices across the Agentic Environment. 

## 1. Mandatory Test Coverage
- **Rule**: Every function, route, and pipeline component that is part of a ticket MUST have at least one corresponding test.
- **Rule**: If a ticket lacks acceptance criteria, the agent MUST explicitly ask the user to define them before proceeding.
- **Rule**: You MUST apply the implementation directives found in `.agents/skills/test-engineering/SKILL.md` (e.g., Test Pyramid, State-Aware Integration, Contract Tests) for all test generation.
