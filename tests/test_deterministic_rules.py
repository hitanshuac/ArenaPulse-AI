from src.domain.deterministic_rules import get_predetermined_suggestions, run_deterministic_translation, run_deterministic_crowd_analysis

def test_get_predetermined_suggestions_high():
    suggestions = get_predetermined_suggestions("corridor", 95, length_m=100, width_m=10, connected_nodes=[])
    assert any("Restrict ALL upstream gate throughput" in s for s in suggestions)

def test_get_predetermined_suggestions_medium():
    suggestions = get_predetermined_suggestions("turnstile", 75, length_m=10, width_m=5, connected_nodes=[])
    assert any("Reduce scanning lanes" in s for s in suggestions)

def test_translation_critical_regex():
    res = run_deterministic_translation("there is a medical emergency in section 102")
    assert res["requires_llm_routing"] is True

def test_translation_normal():
    res = run_deterministic_translation("where is the bathroom")
    assert res["requires_llm_routing"] is False

def test_run_deterministic_crowd_analysis():
    zones = [
        {"zone_id": "Gate A", "current_occupancy": 950, "max_capacity": 1000, "node_type": "turnstile", "connected_nodes": []}
    ]
    res = run_deterministic_crowd_analysis(zones)
    assert "decision" in res
    assert "Rule engine detected 1 zones" in res["decision"]
    assert len(res["execution_trace"]) > 0
    assert len(res["anomalies"]) == 1
    assert res["anomalies"][0]["type"] == "THRESHOLD_BREACH"
    
    zones_medium = [
        {"zone_id": "Gate B", "current_occupancy": 750, "max_capacity": 1000, "node_type": "turnstile", "connected_nodes": []}
    ]
    res2 = run_deterministic_crowd_analysis(zones_medium)
    assert len(res2["anomalies"]) == 0
    assert "Rule engine detected 1 zones" in res2["decision"]


