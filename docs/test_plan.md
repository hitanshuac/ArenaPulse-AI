# Test Plan: Agentic Refactor

**Language / Framework**: Python / Pytest

This test plan enforces the Universal Test Automation constraints and provides strict red-green validation for the new `src/` modules.

## 1. Domain State Management (Unit Tests)
**File**: `tests/test_state.py`

*   **Test Name**: `test_zone_model_validation`
    *   **Type**: Unit
    *   **Setup**: None.
    *   **Action**: Attempt to instantiate `ZoneModel` with negative capacity or invalid types.
    *   **Assertion**: Must raise Pydantic `ValidationError`.

*   **Test Name**: `test_state_manager_singleton`
    *   **Type**: Unit
    *   **Setup**: Instantiate two `StadiumStateManager` objects.
    *   **Action**: Compare the IDs of the two instances.
    *   **Assertion**: Must be identical (singleton pattern).

*   **Test Name**: `test_state_update_occupancy`
    *   **Type**: Unit (Async)
    *   **Setup**: Initialize `StadiumStateManager`.
    *   **Action**: Call `await manager.update_zone_occupancy("Zone A (North Gate)", 500)`.
    *   **Assertion**: Must return `True` and `get_all_zones` should reflect the 500 occupancy.

## 2. Secure LLM Client Interceptor (Integration Tests)
**File**: `tests/test_secure_llm_client.py`

*   **Test Name**: `test_client_memoization_cache`
    *   **Type**: Integration (Mocked AI SDK)
    *   **Setup**: Mock `genai.GenerativeModel.generate_content`.
    *   **Action**: Call `SecureLLMClient.generate_content` twice with identical state arrays.
    *   **Assertion**: First call should hit the mock, second call should return `{"status": "cached"}` and the mock call count should strictly equal 1.

*   **Test Name**: `test_client_quota_exhaustion`
    *   **Type**: Integration
    *   **Setup**: Set `client.daily_calls_made = 15`.
    *   **Action**: Call `SecureLLMClient.generate_content`.
    *   **Assertion**: Must immediately return `{"status": "quota_exhausted"}` without invoking the SDK.

## 3. API Routers (Integration Tests)
**File**: `tests/test_api.py`

*   **Test Name**: `test_update_telemetry_endpoint`
    *   **Type**: Integration
    *   **Setup**: Launch `TestClient` pointing to `src.main.app`.
    *   **Action**: POST to `/api/update-telemetry` with `zone_id` and `current_occupancy`.
    *   **Assertion**: Must return `200 OK` and the subsequent GET to `/api/stadium` must reflect the new value.
