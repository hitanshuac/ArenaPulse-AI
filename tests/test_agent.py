import pytest
from src.domain.agent import VolunteerAgent, validate_spatial_analysis
from src.domain.models import ValidationResult

def test_validate_spatial_analysis_success():
    raw_data = {
        "analyses": [
            {
                "risk_type": "CASCADE_RISK",
                "analysis": "Test analysis",
                "redistributions": [{"zone_id": "Gate A", "reduce_flow_pct": 50, "reasoning": "Congested"}],
                "priority": "HIGH"
            }
        ]
    }
    result = validate_spatial_analysis(raw_data)
    assert result.valid is True
    assert result.data is not None

def test_validate_spatial_analysis_failure():
    raw_data = {"analyses": [{"risk_type": "INVALID_RISK"}]}
    result = validate_spatial_analysis(raw_data)
    assert result.valid is False
    assert "rejected" in result.alerts[0]

def test_volunteer_agent_fallback():
    agent = VolunteerAgent()
    anomalies = [{"zone_id": "Gate A", "type": "CASCADE_RISK"}]
    zones = [{"zone_id": "Gate A", "node_type": "turnstile", "current_occupancy": 950, "max_capacity": 1000, "connected_nodes": ["Plaza A"]}]
    
    result = agent._generate_deterministic_fallback(anomalies, zones, "TEST")
    assert "EDGE COMPUTE FALLBACK" in result["decision"]
    assert "TEST" in result["alerts"][0]
    assert len(result["analyses"]) == 1
    analysis = result["analyses"][0]
    assert analysis["risk_type"] == "CASCADE_RISK"
    assert analysis["priority"] == "HIGH"
    assert len(analysis["redistributions"]) == 1
    assert analysis["redistributions"][0]["reduce_flow_pct"] == 100

def test_analyze_spatial_anomaly_empty():
    agent = VolunteerAgent()
    result = agent.analyze_spatial_anomaly([], [])
    assert "Queue is empty" in result["decision"]

def test_analyze_spatial_anomaly_trust_exhausted():
    agent = VolunteerAgent()
    agent.validation_failure_count = agent.FAILURE_BUDGET
    result = agent.analyze_spatial_anomaly([{"zone_id": "Gate A"}], [{"zone_id": "Gate A"}])
    assert "TRUST BUDGET EXHAUSTED" in result["decision"]

def test_analyze_spatial_anomaly_llm_error(mocker):
    agent = VolunteerAgent()
    mocker.patch.object(agent.llm_client, "generate_content", return_value={"status": "error", "error": "API down"})
    result = agent.analyze_spatial_anomaly([{"zone_id": "Gate A"}], [{"zone_id": "Gate A"}])
    assert "[LLM ERROR] API down" in result["decision"]

def test_analyze_spatial_anomaly_llm_success(mocker):
    agent = VolunteerAgent()
    mock_response = {
        "status": "success",
        "data": {
            "analyses": [
                {
                    "risk_type": "CASCADE_RISK",
                    "analysis": "Test",
                    "redistributions": [{"zone_id": "Gate B", "reduce_flow_pct": 20, "reasoning": "Flow"}],
                    "priority": "MEDIUM"
                }
            ]
        }
    }
    mocker.patch.object(agent.llm_client, "generate_content", return_value=mock_response)
    result = agent.analyze_spatial_anomaly([{"zone_id": "Gate A"}], [{"zone_id": "Gate A", "current_occupancy": 0, "max_capacity": 1}])
    assert "Spatial analysis complete" in result["decision"]
    assert len(result["analyses"]) == 1
    assert len(result["execution_trace"]) > 0

def test_analyze_spatial_anomaly_llm_validation_failure(mocker):
    agent = VolunteerAgent()
    mock_response = {
        "status": "success",
        "data": {"invalid": "schema"}
    }
    mocker.patch.object(agent.llm_client, "generate_content", return_value=mock_response)
    mocker.patch.object(agent.llm_client, "invalidate_cache_for_state")
    
    result = agent.analyze_spatial_anomaly([{"zone_id": "Gate A"}], [{"zone_id": "Gate A", "current_occupancy": 0, "max_capacity": 1}])
    assert "[L1 SCHEMA GATE - REJECTED]" in result["decision"]
    assert agent.validation_failure_count == 1
