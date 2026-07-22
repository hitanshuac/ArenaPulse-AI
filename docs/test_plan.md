# Test Automation Plan

## Overview
This plan defines the test cases to achieve 80%+ line coverage across the repository, targeting untested core modules in accordance with the `.agents/workflows/test-automation.md` workflow.

## 1. Domain Service (`tests/test_service.py`)
| Test Name | Type | Setup | Action | Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `test_run_agent_workflow_success` | Unit | Mock `state_manager` zones and `VolunteerAgent`. | Call `run_agent_workflow()` | Returns correct anomaly count and execution trace. |
| `test_run_agent_workflow_empty` | Unit | Mock `state_manager` returning empty list. | Call `run_agent_workflow()` | Raises `ValueError`. |
| `test_analyze_anomalies_success` | Unit | Mock queue with 1 anomaly, mock `VolunteerAgent` returning redistributions. | Call `analyze_anomalies()` | State manager mitigations applied, queue flushed, correct trace returned. |
| `test_analyze_anomalies_empty` | Unit | Mock empty queue. | Call `analyze_anomalies()` | Returns "NO ANOMALIES" decision immediately. |
| `test_translate_query_critical` | Unit | Mock translation returning `requires_llm_routing=True` | Call `translate_query()` | Calls `state_manager.append_anomaly` with `MEDICAL_ROUTING`. |

## 2. Physics Engine (`tests/test_physics.py`)
| Test Name | Type | Setup | Action | Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `test_build_gravity_map` | Unit | Pass dictionary of connected `ZoneModel` objects. | Call `build_gravity_map()` | Output edges calculate inverse distance correctly. |
| `test_simulate_physics_tick` | Unit | Setup 2 connected zones in INGRESS phase. | Call `simulate_physics_tick()` | Occupancy flows from upstream to downstream correctly, updating `last_updated`. |
| `test_physics_anomaly_generation` | Unit | Setup congested zone with actual_flow < capacity_pph. | Call `simulate_physics_tick()` | Appends `FLOW_MISMATCH` anomaly to the queue. |

## 3. Deterministic Rules (`tests/test_deterministic_rules.py`)
| Test Name | Type | Setup | Action | Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `test_get_predetermined_suggestions_high` | Unit | node_type="corridor", pct=95 | Call `get_predetermined_suggestions` | Returns strict gating and diversion rules. |
| `test_translation_critical_regex` | Unit | query="medical emergency field" | Call `run_deterministic_translation` | Returns `requires_llm_routing=True`. |

## 4. API Endpoints (`tests/test_api_integration.py`)
| Test Name | Type | Setup | Action | Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `test_upload_stadium_data` | Integration | Load CSV fixture from `tests/fixtures/` | POST to `/api/upload-csv` | Returns 200, state manager is updated with fixture rows. |
| `test_stadium_stream` | Integration | Mock `app_service` stream properties | GET `/api/stadium/stream` | Returns valid SSE payload block containing expected JSON. |

## 5. Security Decorators (`tests/test_decorators.py`)
| Test Name | Type | Setup | Action | Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `test_guard_intercepts_call` | Unit | Define dummy func with `@guard` | Call dummy function | `ArenaEngine` extracts payload and logs activity. |
