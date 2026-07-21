import os
from unittest.mock import MagicMock, patch

import pytest

from src.security.secure_llm_client import SecureLLMClient


@pytest.fixture
def secure_client():
    # Force api available for testing
    with patch.dict(os.environ, {"GROQ_API_KEY": "test_key"}):
        with patch("src.security.secure_llm_client.Groq"):
            client = SecureLLMClient()
            client.daily_calls_made = 0
            return client


def test_client_memoization_cache(secure_client):
    """Validates that identical state hashes are served from the cache without hitting the SDK."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"decision": "test"}'
    secure_client.client.chat.completions.create.return_value = mock_response

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
    secure_client.client.chat.completions.create.assert_called_once()

def test_client_quota_exhaustion(secure_client):
    """Validates that the quota limit is aggressively respected."""
    secure_client.daily_calls_made = 5000

    result = secure_client.generate_content("Test", state_data=None)
    assert result["status"] == "quota_exhausted"
    assert result["data"] is None
