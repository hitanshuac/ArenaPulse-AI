import pytest

from app.agent_engine import VolunteerAgent


@pytest.fixture
def agent():
    return VolunteerAgent()

def test_agent_process_telemetry_safe(agent, mocker):
    """Unit: Verifies that safe telemetry doesn't trigger unnecessary alarms."""
    # Mock the underlying Gemini API to prevent real network calls
    mock_model_class = mocker.patch("app.agent_engine.genai.GenerativeModel")
    mock_model_instance = mock_model_class.return_value
    mock_model_instance.generate_content.return_value.text = "[]"

    safe_state = [
        {"zone_id": "Zone A", "current_occupancy": 1000, "max_capacity": 8000, "associated_gates": "G1"}
    ]

    agent.api_available = True
    result = agent.process_telemetry(safe_state)
    assert "decision" in result
    assert "execution_trace" in result

def test_agent_interpret_fan_query_critical(agent, mocker):
    """Unit: Verifies that medical distress queries trigger CRITICAL classification."""
    mock_model_class = mocker.patch("app.agent_engine.genai.GenerativeModel")
    mock_model_instance = mock_model_class.return_value
    mock_model_instance.generate_content.return_value.text = '{"urgency_level": "CRITICAL", "detected_intent": "Medical Emergency", "translated_response_en": "Help is on the way.", "translated_response_es": "La ayuda está en camino."}'

    agent.api_available = True
    result = agent.interpret_fan_query("Doctor, I need help immediately, I can't breathe!")

    assert result["urgency_level"] == "CRITICAL"
    assert "Medical" in result["detected_intent"]
