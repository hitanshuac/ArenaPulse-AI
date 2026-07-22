import asyncio

import pytest
from pydantic import ValidationError

from src.domain.models import ZoneModel
from src.domain.state import StadiumStateManager


def test_zone_model_validation():
    """Validates that Pydantic enforces correct schemas and rejects invalid metric values."""
    # Should raise error for negative current_occupancy
    with pytest.raises(ValidationError):
        ZoneModel(zone_id="Gate 1", current_occupancy=-100, max_capacity=5000, associated_gates="Gate 1", velocity=0)

    # Should raise error for zero max_capacity
    with pytest.raises(ValidationError):
        ZoneModel(zone_id="Gate 1", current_occupancy=100, max_capacity=0, associated_gates="Gate 1", velocity=0)


def test_state_manager_singleton():
    """Validates that StadiumStateManager operates as a Singleton."""
    manager1 = StadiumStateManager()
    manager2 = StadiumStateManager()

    assert id(manager1) == id(manager2), "Instances are not the same Singleton object"


def test_state_update_occupancy():
    """Validates the thread-safe occupancy update logic."""
    manager = StadiumStateManager()
    # Force initialize the state cleanly for testing
    manager._init_state()

    async def run_test():
        success = await manager.update_zone_occupancy("Gate A", 500)
        assert success is True

        all_zones = await manager.get_all_zones()
        zone_a = next(z for z in all_zones if z["zone_id"] == "Gate A")

        assert zone_a["current_occupancy"] == 500

        # Test invalid zone
        success_invalid = await manager.update_zone_occupancy("NonExistentZone", 100)
        assert success_invalid is False

    asyncio.run(run_test())

def test_anomaly_queue_operations():
    manager = StadiumStateManager()
    manager._init_state()
    async def run_test():
        await manager.append_anomaly({"type": "FLOW_MISMATCH", "zone_id": "Gate A"})
        queue = await manager.get_anomaly_queue()
        assert len(queue) == 1
        assert queue[0]["zone_id"] == "Gate A"
        
        flushed = await manager.flush_anomaly_queue()
        assert len(flushed) == 1
        assert len(await manager.get_anomaly_queue()) == 0
    asyncio.run(run_test())

def test_snapshot_and_rollback():
    manager = StadiumStateManager()
    manager._init_state()
    async def run_test():
        await manager.update_zone_occupancy("Gate A", 999)
        await manager.snapshot_state()
        await manager.update_zone_occupancy("Gate A", 100)
        await manager.rollback_state()
        zones = await manager.get_all_zones()
        zone_a = next(z for z in zones if z["zone_id"] == "Gate A")
        assert zone_a["current_occupancy"] == 999
        
        assert await manager.rollback_state() is False # nothing to rollback
    asyncio.run(run_test())

def test_metadata_and_phase():
    manager = StadiumStateManager()
    manager._init_state()
    async def run_test():
        await manager.set_phase("MATCH")
        meta = await manager.get_system_metadata()
        assert meta["current_phase"] == "MATCH"
        assert meta["match_minute"] == 45
        assert meta["match_running"] is True
    asyncio.run(run_test())

def test_update_mitigation():
    manager = StadiumStateManager()
    manager._init_state()
    async def run_test():
        success = await manager.update_mitigation("Gate A", "Reduce flow")
        assert success is True
        zones = await manager.get_all_zones()
        zone_a = next(z for z in zones if z["zone_id"] == "Gate A")
        assert zone_a["mitigation_active"] == "Reduce flow"
        
        assert await manager.update_mitigation("Invalid", "X") is False
    asyncio.run(run_test())

def test_apply_bulk_update():
    manager = StadiumStateManager()
    manager._init_state()
    async def run_test():
        data = [{"zone_id": "Gate A", "node_type": "turnstile", "current_occupancy": 50, "max_capacity": 100, "associated_gates": "", "velocity": 0}]
        await manager.apply_bulk_update(data)
        zones = await manager.get_all_zones()
        assert len(zones) == 1
        assert zones[0]["zone_id"] == "Gate A"
    asyncio.run(run_test())

def test_simulate_iot_tick():
    manager = StadiumStateManager()
    manager._init_state()
    async def run_test():
        manager.match_running = True
        manager.current_phase = "INGRESS"
        manager.match_minute = 44
        await manager.simulate_iot_tick()
        assert manager.match_minute == 45
        assert manager.current_phase == "MATCH" # Auto-transition
        
        manager.match_minute = 89
        await manager.simulate_iot_tick()
        assert manager.match_minute == 90
        assert manager.current_phase == "EGRESS" # Auto-transition
        
        manager.match_minute = 119
        await manager.simulate_iot_tick()
        assert manager.match_minute == 120
        assert manager.match_running is False # Match over
        
        alerts = await manager.flush_alerts()
        assert len(alerts) > 0
    asyncio.run(run_test())

