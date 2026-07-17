import os
from unittest.mock import MagicMock, patch

import pytest

from src.security.secure_llm_client import SecureLLMClient


@pytest.fixture
def secure_client():
    # Force api available for testing
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        client = SecureLLMClient()
        return client

@patch("src.security.secure_llm_client.genai.GenerativeModel")
def test_client_memoization_cache(mock_model_class, secure_client):
    """Validates that identical state hashes are served from the cache without hitting the SDK."""
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"decision": "test"}'
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance

    state_data = [{"zone_id": "test", "occupancy": 100}]

    # First call - should hit mock
    result1 = secure_client.generate_content("Analyze this", state_data=state_data)
    assert result1["status"] == "success"
    assert result1["data"] == {"decision": "test"}
    assert secure_client.daily_calls_made == 1

    # Second call - should hit cache
    result2 = secure_client.generate_content("Analyze this", state_data=state_data)
    assert result2["status"] == "cached"
    assert result2["data"] == {"decision": "test"}

    # Still 1 call made!
    assert secure_client.daily_calls_made == 1
    mock_model_instance.generate_content.assert_called_once()

def test_client_quota_exhaustion(secure_client):
    """Validates that the quota limit is aggressively respected."""
    secure_client.daily_calls_made = 15

    result = secure_client.generate_content("Test", state_data=None)
    assert result["status"] == "quota_exhausted"
    assert result["data"] is None
