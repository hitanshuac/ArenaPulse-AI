# Handover & Architectural Context: ArenaPulse AI (v1)

This handover document provides structural, logical, and execution context for the Antigravity IDE and its autonomous AI coding agents. Read this file before initiating any refactoring, feature extension, or prompt modifications.

---

## 1. Project Intent & Scope
* **Target Persona:** Stadium Volunteer (On-ground operations staff at FIFA World Cup 2026).
* **Core Problem Verticals:** Real-Time Crowd Management & Context-Aware Multilingual Field Translation.
* **Architectural Pivot:** This is a data-driven, event-based operational dashboard. It is **not** a conversational chatbot. The system continuously ingests time-series telemetry data and triggers background agentic workflows.

---

## 2. Directory & Component Layout
All workspace files are modular and kept lightweight to stay well below the 10 MB repository limit.

```text
├── requirements.txt            # Minimal dependencies (FastAPI, google-generativeai, pillow, pytest)
├── .gitignore                  # Active patterns to exclude .venv, Pycache, and IDE configs
├── tests/                      # Active test suites for API, state, security, and architecture
├── static/
│   └── index.html              # Frontend dashboard with live Chart.js time-series logic
├── data/                       # SRE Observability and generated output logs
└── src/
    ├── main.py                 # FastAPI backend, background simulated IoT
    ├── routers/api.py          # Telemetry and dashboard routing
    ├── domain/                 # Core operational logic
    │   ├── agent.py            # AI simulation agent
    │   ├── models.py           # Pydantic data schemas
    │   ├── physics.py          # Gravity-based physics flow engine
    │   ├── state.py            # DAG spatial state manager
    │   └── deterministic_rules.py # Local fallback safety engine & physical validations
    └── security/
        └── secure_llm_client.py # Cached Gemini interactions for quota optimization