import asyncio
import random
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ZoneModel(BaseModel):
    zone_id: str = Field(..., description="Unique ID of the stadium zone")
    current_occupancy: int = Field(..., ge=0, description="Current occupancy metric")
    max_capacity: int = Field(..., gt=0, description="Max safe capacity threshold")
    associated_gates: str = Field(..., description="Physical gates serving the zone")
    velocity: int = Field(0, description="Rate of change (fans/min)")
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z", description="ISO timestamp")
    
    # Topological mapping
    upstream_nodes: list[str] = Field(default_factory=list, description="IDs of zones that flow into this zone")
    downstream_nodes: list[str] = Field(default_factory=list, description="IDs of zones this zone flows into")
    
    # AI state
    mitigation_active: Optional[str] = Field(None, description="Active AI mitigation (e.g. 'Redirecting', 'Barriers Active')")

class StadiumStateManager:
    """
    Thread-safe Singleton state manager.
    Prevents race conditions between API endpoints and Background IoT simulation.
    Now operates on a spatial DAG to support upstream mitigation routing.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self._lock = asyncio.Lock()
        self._zones: dict[str, ZoneModel] = {
            "Main Concourse": ZoneModel(
                zone_id="Main Concourse", current_occupancy=4000, max_capacity=20000, 
                associated_gates="All", downstream_nodes=["North Corridor", "East Corridor"]
            ),
            "North Corridor": ZoneModel(
                zone_id="North Corridor", current_occupancy=1000, max_capacity=4000, 
                associated_gates="Internal N", upstream_nodes=["Main Concourse"], downstream_nodes=["North Gate"]
            ),
            "East Corridor": ZoneModel(
                zone_id="East Corridor", current_occupancy=1200, max_capacity=4000, 
                associated_gates="Internal E", upstream_nodes=["Main Concourse"], downstream_nodes=["East Gate"]
            ),
            "North Gate": ZoneModel(
                zone_id="North Gate", current_occupancy=3200, max_capacity=8000, 
                associated_gates="Gates 1-2", upstream_nodes=["North Corridor"]
            ),
            "East Gate": ZoneModel(
                zone_id="East Gate", current_occupancy=5100, max_capacity=8000, 
                associated_gates="Gates 3-4", upstream_nodes=["East Corridor"]
            )
        }

    async def get_all_zones(self) -> list[dict[str, Any]]:
        async with self._lock:
            return [z.model_dump() for z in self._zones.values()]

    async def update_zone_occupancy(self, zone_id: str, new_occupancy: int) -> bool:
        async with self._lock:
            if zone_id in self._zones:
                self._zones[zone_id].current_occupancy = max(0, new_occupancy)
                self._zones[zone_id].last_updated = datetime.utcnow().isoformat() + "Z"
                return True
            return False

    async def update_mitigation(self, zone_id: str, mitigation: Optional[str]) -> bool:
        async with self._lock:
            if zone_id in self._zones:
                self._zones[zone_id].mitigation_active = mitigation
                self._zones[zone_id].last_updated = datetime.utcnow().isoformat() + "Z"
                return True
            return False

    async def apply_bulk_update(self, new_state: list[dict[str, Any]]):
        async with self._lock:
            self._zones.clear()
            for row in new_state:
                zone = ZoneModel(**row)
                self._zones[zone.zone_id] = zone

    async def simulate_iot_tick(self):
        async with self._lock:
            # 1. Add random influx to the root node (Main Concourse)
            root = self._zones["Main Concourse"]
            addition = random.randint(50, 150)
            root.current_occupancy = min(root.max_capacity, root.current_occupancy + addition)
            root.velocity = addition * 10
            root.last_updated = datetime.utcnow().isoformat() + "Z"

            # 2. Propagate traffic downstream
            # If a corridor has a mitigation (e.g. barrier), flow is restricted
            for zone_id, zone in self._zones.items():
                if zone.upstream_nodes:
                    total_influx = 0
                    for up_id in zone.upstream_nodes:
                        up_zone = self._zones[up_id]
                        # Transfer 10% of upstream occupancy downwards
                        transfer = int(up_zone.current_occupancy * 0.10)
                        
                        # Throttle transfer if upstream has a mitigation active
                        if up_zone.mitigation_active:
                            transfer = int(transfer * 0.1) # 90% blocked
                            
                        # Remove from upstream, add to current
                        up_zone.current_occupancy = max(0, up_zone.current_occupancy - transfer)
                        total_influx += transfer
                    
                    # Also add a baseline random influx from local gates
                    local_addition = random.randint(10, 30)
                    new_occ = min(zone.max_capacity, zone.current_occupancy + total_influx + local_addition)
                    
                    actual_addition = new_occ - zone.current_occupancy
                    zone.current_occupancy = new_occ
                    zone.velocity = actual_addition * 5
                    zone.last_updated = datetime.utcnow().isoformat() + "Z"
