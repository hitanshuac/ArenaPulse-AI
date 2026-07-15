---
trigger: active
---

# Hack2Skill Challenge Rules & Instructions (Prompt Wars Virtual - Challenge 4)

This master rule document governs the entire repository, directly echoing the official Hack2Skill Challenge 4 instructions. All agentic workflows, architecture designs, and development processes MUST strictly align with these mandates.

## 1. Strict Git & Repository Constraints
Failure to follow these repository boundaries results in automatic evaluation failure.
* **Visibility:** The GitHub repository MUST be set to **Public**.
* **Branch Limit:** The repository MUST contain **exactly one branch** (strictly "main" or "master"). You are forbidden from creating, suggesting, or checking out new Git branches. Keep commits strictly linear (no complex merge/rebase workflows).
* **Size Constraint:** The total repository footprint MUST be **strictly under 10 MB**.
* **Clean Code Practices (No Bloat):** Ensure your ".gitignore" is active. Do not commit heavy dependency folders, node packages ("node_modules"), virtual environments (".venv"), database files (".duckdb"), large datasets, or raw telemetry.

## 2. Challenge 4 Mandates: Smart Stadiums
* **Theme:** GenAI-enabled stadium operations and overall tournament experience for fans, organizers, volunteers, or venue staff during the FIFA World Cup 2026.
* **Mandatory GenAI Integration:** GenAI usage must be central to the application's core feature. It must reason over unstructured data, classify intents, or generate dynamic outputs.
* **Data Ingestion:** The application must process incoming operational telemetry dynamically. Avoid mocking major systems with simple hardcoded static pages.
* **Google Services Score:** Maximize score by incorporating **Google AI Studio (Gemini SDK)**, Google Maps API, or Firebase directly.

## 3. Submission Contract & The README.md
* **Attempt Cap:** Maximum of 3 submission attempts (only the latest attempt counts).
* **Required Links:** A live deployment URL, a Public GitHub Repository link, and a LinkedIn Documentation post detailing strategy and division of AI vs hand-coded labor.
* **README.md Contract:** The README MUST include these exact sections prominently at the top:
  1. **Vertical/Persona:** State clearly the chosen Challenge 4 vertical/persona (e.g., Stadium Operations / Safety Coordinator).
  2. **Approach & Logic:** Explain the architectural pipeline (e.g., DuckDB integration, data flow).
  3. **Assumptions Made:** List any technical or business assumptions made during development.

## 4. Evaluation Criteria (Code Standards)
Submissions will be reviewed and must pass these quality gates:
* **Efficiency:** Optimal resource usage, low processing overhead. Use vectorized operations (PyArrow/DuckDB) over standard Python loops.
* **Security:** Secure API key handling (no hardcoding) and defensive error-handling.
* **Testing:** Robust handling of system edge cases (malformed data, empty states, and API timeouts). Ensure components are modular and testable.
* **Accessibility:** Any frontend UI (HTML/React) must include semantic tags, ARIA labels, screen-reader support, and proper contrast for enterprise accessibility standards.
* **Code Quality & Problem Alignment:** High readability, maintainability, and deep focus on logical reasoning over data trends (Explainable AI / XAI).
