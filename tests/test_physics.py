from src.domain.physics import build_gravity_map, simulate_physics_tick
from src.domain.models import ZoneModel

def test_build_gravity_map():
    zones = {
        "S1": ZoneModel(zone_id="S1", node_type="seating", current_occupancy=0, max_capacity=100, associated_gates=""),
        "C1": ZoneModel(zone_id="C1", node_type="corridor", current_occupancy=0, max_capacity=100, associated_gates=""),
        "T1": ZoneModel(zone_id="T1", node_type="turnstile", current_occupancy=0, max_capacity=100, associated_gates=""),
        "Plaza1": ZoneModel(zone_id="Plaza1", node_type="external", current_occupancy=0, max_capacity=100, associated_gates=""),
        "E1": ZoneModel(zone_id="E1", node_type="external", current_occupancy=0, max_capacity=100, associated_gates=""),
        "A1": ZoneModel(zone_id="A1", node_type="amenity", current_occupancy=0, max_capacity=100, associated_gates="")
    }
    gmap = build_gravity_map(zones)
    assert gmap["S1"] == 0
    assert gmap["A1"] == 1
    assert gmap["C1"] == 2
    assert gmap["T1"] == 3
    assert gmap["Plaza1"] == 3.5
    assert gmap["E1"] == 4

def test_simulate_physics_tick_ingress():
    # INGRESS: flow from high gravity to low gravity
    # External (4) -> Turnstile (3) -> Corridor (2) -> Seating (0)
    zones = {
        "E1": ZoneModel(zone_id="E1", node_type="external", current_occupancy=100, max_capacity=1000, throughput_capacity_pph=600, connected_nodes=["T1"], associated_gates=""),
        "T1": ZoneModel(zone_id="T1", node_type="turnstile", current_occupancy=0, max_capacity=1000, throughput_capacity_pph=600, connected_nodes=["C1"], associated_gates=""),
        "C1": ZoneModel(zone_id="C1", node_type="corridor", current_occupancy=0, max_capacity=1000, throughput_capacity_pph=600, connected_nodes=["S1"], associated_gates=""),
        "S1": ZoneModel(zone_id="S1", node_type="seating", current_occupancy=0, max_capacity=1000, throughput_capacity_pph=600, connected_nodes=[], associated_gates="")
    }
    
    gmap = build_gravity_map(zones)
    anomaly_queue = []
    alerts = []
    
    simulate_physics_tick(zones, current_phase="INGRESS", gravity_map=gmap, anomaly_queue=anomaly_queue, alerts=alerts)
    
    # E1 flows 10% of occupancy to T1 => 10
    # But throughput capacity limits it? max_flow_per_minute = 600/60 = 10.
    # Flow amount should be 10. E1 should have 90, T1 should have 10.
    assert zones["E1"].current_occupancy == 90
    assert zones["T1"].current_occupancy == 10

def test_physics_anomaly_generation():
    # Setup congested zone where actual_flow < capacity_pph and adjacent zones are heavily congested
    zones = {
        "C1": ZoneModel(zone_id="C1", node_type="corridor", current_occupancy=100, max_capacity=1000, throughput_capacity_pph=600, connected_nodes=["S1"], associated_gates=""),
        "S1": ZoneModel(zone_id="S1", node_type="seating", current_occupancy=1000, max_capacity=1000, throughput_capacity_pph=600, connected_nodes=[], associated_gates="")
    }
    # S1 is 90% congested. C1 has actual flow = 0 (since we haven't flowed yet, or let's let it flow)
    gmap = build_gravity_map(zones)
    anomaly_queue = []
    alerts = []
    
    simulate_physics_tick(zones, current_phase="INGRESS", gravity_map=gmap, anomaly_queue=anomaly_queue, alerts=alerts)
    
    # C1 will try to flow to S1.
    # Check if FLOW_MISMATCH anomaly is generated for C1 or S1
    # Actually FLOW_MISMATCH is if actual flow is low but adjacent is heavily congested.
    assert any("bottleneck detected" in a and "C1" in a for a in alerts)
    assert zones["C1"].mitigation_active is not None
    assert "Flow rebalance" in zones["C1"].mitigation_active

def test_simulate_physics_tick_egress():
    # EGRESS: flow from low gravity to high gravity
    zones = {
        "S1": ZoneModel(zone_id="S1", node_type="seating", current_occupancy=100, max_capacity=1000, throughput_capacity_pph=600, connected_nodes=["C1"], associated_gates=""),
        "C1": ZoneModel(zone_id="C1", node_type="corridor", current_occupancy=0, max_capacity=1000, throughput_capacity_pph=600, connected_nodes=[], associated_gates="")
    }
    
    gmap = build_gravity_map(zones)
    anomaly_queue = []
    alerts = []
    
    simulate_physics_tick(zones, current_phase="EGRESS", gravity_map=gmap, anomaly_queue=anomaly_queue, alerts=alerts)
    
    # S1 flows 15% to C1 => 15, but throughput is 10. So flows 10.
    assert zones["S1"].current_occupancy == 90
    assert zones["C1"].current_occupancy == 10
