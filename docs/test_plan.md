# Universal Test Plan

**Target Framework:** Pytest (FastAPI / Python)
**Target Modules:** `app/main.py`, `app/agent_engine.py` (Missing Coverage)

## Fixture Plan (Phase 2.5 I/O Gate)
Since `app/main.py` processes CSV uploads, the following fixtures will be created in `tests/fixtures/`:
1. `stadium_canonical.csv` (Valid schema)
2. `stadium_invalid.csv` (Malformed/Missing columns)
3. `stadium_empty.csv` (Empty edges case)

## Test Cases

### 1. `test_get_stadium_state`
- **Test Type:** Unit
- **Setup:** FastAPI `TestClient` initialized.
- **Action:** `GET /api/stadium`
- **Assertion:** Returns 200 OK. Matches default `active_stadium_state` schema.

### 2. `test_update_telemetry`
- **Test Type:** Unit
- **Setup:** FastAPI `TestClient` initialized.
- **Action:** `POST /api/update-telemetry` with `zone_id="Zone A (North Gate)"` and `current_occupancy=4500`.
- **Assertion:** Returns 200 OK. State updates successfully.

### 3. `test_update_telemetry_not_found`
- **Test Type:** Unit
- **Setup:** FastAPI `TestClient` initialized.
- **Action:** `POST /api/update-telemetry` with invalid `zone_id="Ghost Zone"`.
- **Assertion:** Returns 404 Not Found.

### 4. `test_upload_csv_success`
- **Test Type:** Integration (I/O)
- **Setup:** Load `tests/fixtures/stadium_canonical.csv`.
- **Action:** `POST /api/upload-csv` with file payload.
- **Assertion:** Returns 200 OK. `active_stadium_state` is overwritten with fixture data.

### 5. `test_upload_csv_invalid_schema`
- **Test Type:** Integration (I/O)
- **Setup:** Load `tests/fixtures/stadium_invalid.csv`.
- **Action:** `POST /api/upload-csv` with file payload.
- **Assertion:** Returns 400 Bad Request. Exception caught gracefully.

### 6. `test_agent_engine_process_telemetry_safe`
- **Test Type:** Unit
- **Setup:** Instantiate `VolunteerAgent`. Ensure `api_available` is bypassed or mocked safely.
- **Action:** Call `process_telemetry()` with zones <80% capacity.
- **Assertion:** Returns safe decision string. Execution trace is empty or notes no action required.

### 7. `test_agent_engine_translate_critical`
- **Test Type:** Unit
- **Setup:** Instantiate `VolunteerAgent`.
- **Action:** Call `interpret_fan_query("Doctor, help!")`.
- **Assertion:** `urgency_level` == "CRITICAL".
