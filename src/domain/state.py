import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ZoneModel(BaseModel):
    zone_id: str = Field(..., description="Unique ID of the stadium zone")
    current_occupancy: int = Field(..., ge=0, description="Current occupancy metric")
    max_capacity: int = Field(..., gt=0, description="Max safe capacity threshold")
    associated_gates: str = Field(..., description="Physical gates serving the zone")
    velocity: int = Field(0, description="Rate of change (fans/min)")

class StadiumStateManager:
    """
    Thread-safe Singleton state manager.
    Prevents race conditions between API endpoints and Background IoT simulation.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self._lock = asyncio.Lock()
        self._zones: Dict[str, ZoneModel] = {
            "Zone A (North Gate)": ZoneModel(zone_id="Zone A (North Gate)", current_occupancy=3200, max_capacity=8000, associated_gates="Gates 1-2", velocity=0),
            "Zone B (East Gate)": ZoneModel(zone_id="Zone B (East Gate)", current_occupancy=5100, max_capacity=8000, associated_gates="Gates 3-4", velocity=0),
            "Zone C (South Gate)": ZoneModel(zone_id="Zone C (South Gate)", current_occupancy=1500, max_capacity=8000, associated_gates="Gates 5-6", velocity=0)
        }

    async def get_all_zones(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return [z.model_dump() for z in self._zones.values()]

    async def update_zone_occupancy(self, zone_id: str, new_occupancy: int) -> bool:
        async with self._lock:
            if zone_id in self._zones:
                self._zones[zone_id].current_occupancy = max(0, new_occupancy)
                return True
            return False

    async def apply_bulk_update(self, new_state: List[Dict[str, Any]]):
        async with self._lock:
            self._zones.clear()
            for row in new_state:
                zone = ZoneModel(**row)
                self._zones[zone.zone_id] = zone

    async def simulate_iot_tick(self):
        import random
        async with self._lock:
            for zone in self._zones.values():
                addition = random.randint(10, 40)
                new_occ = min(zone.max_capacity, zone.current_occupancy + addition)
                actual_addition = new_occ - zone.current_occupancy
                zone.current_occupancy = new_occ
                zone.velocity = actual_addition * 15
