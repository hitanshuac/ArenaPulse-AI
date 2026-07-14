---
name: SAST and Evaluator Compliance
description: Strict engineering rules to achieve zero-defect compliance against Automated Evaluators, AI Code Analyzers, and CI/CD pipelines.
---

# Automated SAST & Evaluator Standards

## 1. Problem Statement Alignment
- You MUST use the exact, verbatim keywords from the project requirements in the `README.md` and module-level docstrings.
- Always include explicit sections mapping the solution to the exact constraints.

## 2. Accessibility (A11y)
- All UI inputs must contain ARIA-compliant labels or tooltips.
- In Streamlit, always provide the `help="description"` parameter to all input widgets (`st.text_input`, `st.button`, etc.). 

## 3. Efficiency
- Heavy generation functions must be memoized, and threads must be non-blocking.
- Decorate LLM calls with `@st.cache_data` or `@lru_cache`. Rely on native UI frameworks for retry loops rather than halting the main thread.

## 4. Code Quality (AST Strictness)
- Code must be modular, type-hinted, and free of dynamic execution or raw HTML injections. 
- Use `ast.literal_eval()` or native arithmetic instead of `eval()`.
- Rely exclusively on native Streamlit widgets instead of injecting custom HTML/CSS strings (`unsafe_allow_html=True`).
- Encapsulate all logic into single-responsibility functions (e.g., `def render_ui()`).

## 5. Security (Prompt Injection)
- Implement an explicit `sanitize_input` function that strips HTML tags, escapes malicious characters (`< > { }`), and strictly truncates strings to a safe length (e.g., 500 chars) before LLM ingestion.

## 6. Testing Coverage
- Ensure tests reside in `tests/` (not `src/tests/`). Provide isolated unit tests for pure functions alongside UI integration tests.
