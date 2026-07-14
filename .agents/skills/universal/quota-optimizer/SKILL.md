---
name: Quota Optimizer
description: Strategies and heuristics to prevent excessive API quota drain during autonomous agent execution.
---

# Quota Optimization & Anti-Drain

These implementation heuristics prevent excessive API quota drain during autonomous agent execution.

## 1. Placeholders for Missing Data
- If data is missing from the target file, immediately use a placeholder (e.g., `[NAME]`) or stop and ask the user, rather than performing exhaustive workspace recursive searches.

## 2. Comprehensive Debugging Scripts
- If you need to debug data processing, write a single comprehensive script that outputs all necessary diagnostic information at once, run it, and read the output. Avoid micro-execution step-by-step REPL loops.

## 3. Structural Validation
- Rely on structural checks or output files for UI validation. Reserve the `browser_subagent` exclusively for explicitly stated UI/UX validation goals.

## 4. Optimistic Execution
- Assume standard Python libraries or node modules are available or installable as needed. Write the code, run it, and catch the `ImportError` or `ModuleNotFoundError` if it fails, rather than running arbitrary checking commands first.
