import pytest

from arenapulse import (
    ArenaEngine,
    CrowdFlowRateRule,
    ExecutionError,
    StadiumCapacityRule,
    StadiumStateTransitionRule,
)


def test_stadium_capacity_rule():
    engine = ArenaEngine("FIFA-Stadium-Engine")
    engine.add_rule(StadiumCapacityRule(critical_threshold_pct=95.0))

    # Safe occupancy (80%)
    res = engine.verify_and_execute("update_occupancy", {"zone_id": "Gate A", "current_occupancy": 800, "max_capacity": 1000})
    assert res["status"] == "SUCCESS"

    # Critical overcrowding (98%) -> Must be blocked by deterministic safety gate
    with pytest.raises(ExecutionError) as exc_info:
        engine.verify_and_execute("update_occupancy", {"zone_id": "Gate A", "current_occupancy": 980, "max_capacity": 1000})
    assert "CRITICAL OVERCROWDING" in str(exc_info.value)


def test_crowd_flow_rate_rule():
    engine = ArenaEngine("FIFA-Stadium-Engine")
    engine.add_rule(CrowdFlowRateRule())

    # Safe inflow rate (30 fans/min into corridor)
    res = engine.verify_and_execute("adjust_flow", {"inflow_rate": 30, "throughput_capacity_pph": 3000})
    assert res["status"] == "SUCCESS"

    # Excessive inflow rate (120 fans/min > 50 fans/min capacity) -> Stampede risk blocked
    with pytest.raises(ExecutionError) as exc_info:
        engine.verify_and_execute("adjust_flow", {"inflow_rate": 120, "throughput_capacity_pph": 3000})
    assert "STAMPEDE RISK" in str(exc_info.value)


def test_stadium_state_transition_rule():
    engine = ArenaEngine("FIFA-Stadium-Engine")
    engine.add_rule(StadiumStateTransitionRule())

    # Valid phase shift: INGRESS -> MATCH
    res = engine.verify_and_execute("set_match_phase", {"current_phase": "INGRESS", "target_phase": "MATCH"})
    assert res["status"] == "SUCCESS"

    # Illegal phase jump: INGRESS -> EGRESS directly -> Blocked
    with pytest.raises(ExecutionError) as exc_info:
        engine.verify_and_execute("set_match_phase", {"current_phase": "INGRESS", "target_phase": "EGRESS"})
    assert "Illegal match phase jump" in str(exc_info.value)
