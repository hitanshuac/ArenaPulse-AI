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
├── requirements.txt            # Minimal dependencies (FastAPI, google-generativeai)
├── .gitignore                  # Active patterns to exclude .venv, Pycache, and IDE configs
├── tests/
│   └── test_app.py             # Active unit testing suite for fallback validation
├── static/
│   └── index.html              # Frontend dashboard with live Chart.js time-series logic
└── app/
    ├── __init__.py
    ├── main.py                 # FastAPI backend, CSV processing, & telemetry routes
    ├── agent_engine.py         # Google AI Studio (Gemini 1.5 Flash) Orchestrator & Tool Caller
    └── deterministic_rules.py  # Local fallback safety engine (Offline / API failure resilience)