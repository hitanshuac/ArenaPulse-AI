import pytest
import asyncio
from pydantic import ValidationError
from src.domain.state import ZoneModel, StadiumStateManager

def test_zone_model_validation():
    """Validates that Pydantic enforces correct schemas and rejects invalid metric values."""
    # Should raise error for negative current_occupancy
    with pytest.raises(ValidationError):
        ZoneModel(
            zone_id="Gate 1",
            current_occupancy=-100,
            max_capacity=5000,
            associated_gates="Gate 1",
            velocity=0
        )
    
    # Should raise error for zero max_capacity
    with pytest.raises(ValidationError):
        ZoneModel(
            zone_id="Gate 1",
            current_occupancy=100,
            max_capacity=0,
            associated_gates="Gate 1",
            velocity=0
        )

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
        success = await manager.update_zone_occupancy("Zone A (North Gate)", 500)
        assert success is True
        
        all_zones = await manager.get_all_zones()
        zone_a = next(z for z in all_zones if z["zone_id"] == "Zone A (North Gate)")
        
        assert zone_a["current_occupancy"] == 500
        
        # Test invalid zone
        success_invalid = await manager.update_zone_occupancy("NonExistentZone", 100)
        assert success_invalid is False
        
    asyncio.run(run_test())
