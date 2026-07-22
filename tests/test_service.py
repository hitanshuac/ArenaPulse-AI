import pytest
from unittest.mock import AsyncMock, MagicMock

from src.domain.service import StadiumApplicationService

@pytest.fixture
def mock_state_manager():
    manager = AsyncMock()
    manager.get_all_zones.return_value = [{"zone_id": "Zone A"}]
    manager.get_anomaly_queue.return_value = []
    manager.snapshot_state = AsyncMock()
    manager.update_mitigation = AsyncMock(return_value=True)
    manager.flush_anomaly_queue = AsyncMock()
    manager.append_anomaly = AsyncMock()
    return manager

@pytest.fixture
def mock_stadium_agent():
    agent = MagicMock()
    agent.process_telemetry.return_value = {"decision": "Processed", "execution_trace": []}
    agent.analyze_spatial_anomaly.return_value = {
        "decision": "Analyzed",
        "analyses": [{"redistributions": [{"zone_id": "Zone A", "reduce_flow_pct": 10, "reasoning": "Congested"}]}],
        "execution_trace": []
    }
    agent.interpret_fan_query.return_value = {"requires_llm_routing": False}
    return agent

@pytest.fixture
def app_service(mock_state_manager, mock_stadium_agent):
    service = StadiumApplicationService()
    service.state_manager = mock_state_manager
    service.stadium_agent = mock_stadium_agent
    return service

import asyncio

def test_run_agent_workflow_success(app_service, mock_state_manager):
    # Setup anomalies in queue
    mock_state_manager.get_anomaly_queue.return_value = [
        {"type": "FLOW_MISMATCH", "zone_id": "Zone A", "actual_flow_pph": 100, "capacity_pph": 50},
        {"type": "CASCADE_RISK", "zone_id": "Zone B", "action": "Lockdown"}
    ]
    result = asyncio.run(app_service.run_agent_workflow())
    
    assert result["anomaly_count"] == 2
    assert "Processed" in result["decision"]
    assert any("actual flow 100" in trace for trace in result["execution_trace"])
    assert any("Lockdown" in trace for trace in result["execution_trace"])

def test_run_agent_workflow_empty(app_service, mock_state_manager):
    mock_state_manager.get_all_zones.return_value = []
    with pytest.raises(ValueError):
        asyncio.run(app_service.run_agent_workflow())

def test_analyze_anomalies_success(app_service, mock_state_manager):
    mock_state_manager.get_anomaly_queue.return_value = [{"type": "FLOW_MISMATCH", "zone_id": "Zone A"}]
    
    result = asyncio.run(app_service.analyze_anomalies())
    
    mock_state_manager.update_mitigation.assert_called_once_with("Zone A", "Flow reduced 10%: Congested")
    mock_state_manager.flush_anomaly_queue.assert_called_once()
    assert "Applied: 1 flow redistributions" in result["execution_trace"][-1]

def test_analyze_anomalies_empty(app_service, mock_state_manager):
    mock_state_manager.get_anomaly_queue.return_value = []
    result = asyncio.run(app_service.analyze_anomalies())
    assert "Queue is empty" in result["decision"]

def test_translate_query_critical(app_service, mock_state_manager, mock_stadium_agent):
    mock_stadium_agent.interpret_fan_query.return_value = {
        "requires_llm_routing": True,
        "translated_response_en": "Medical Emergency"
    }
    
    result = asyncio.run(app_service.translate_query("urgent need help"))
    
    assert result["requires_llm_routing"] is True
    mock_state_manager.append_anomaly.assert_called_once()
    args, kwargs = mock_state_manager.append_anomaly.call_args
    assert args[0]["type"] == "MEDICAL_ROUTING"

def test_translate_query_empty(app_service):
    with pytest.raises(ValueError):
        asyncio.run(app_service.translate_query("   "))
