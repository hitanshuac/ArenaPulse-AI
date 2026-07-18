import asyncio
import logging
import random
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


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
    mitigation_active: str | None = Field(None, description="Active AI mitigation (e.g. 'Redirecting', 'Barriers Active')")


class StadiumStateManager:
    """
    Thread-safe Singleton state manager with closed-loop validation.
    Prevents race conditions between API endpoints and Background IoT simulation.
    Operates on a spatial DAG to support upstream mitigation routing.

    Closed-Loop Layers:
        L2: Topology Gate — validates mitigations target upstream nodes.
        L3: Outcome Monitor — detects ineffective mitigations via velocity tracking.
    """
    _instance = None

    # L3: Maximum ticks a mitigation can be active without reducing downstream occupancy
    MAX_INEFFECTIVE_TICKS = 3

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
        # State snapshot for rollback
        self._snapshot: dict[str, ZoneModel] | None = None

        # L3: Outcome monitor — tracks consecutive ineffective ticks per zone
        self._mitigation_tick_counter: dict[str, int] = {}
        self._mitigation_baseline_occupancy: dict[str, dict[str, int]] = {}

        # System alerts buffer — consumed and flushed by SSE stream
        self._alerts: list[str] = []

    # ------------------------------------------------------------------
    # State Snapshot & Rollback
    # ------------------------------------------------------------------

    async def snapshot_state(self):
        """Deep-copy current zones for rollback if LLM-driven mutations fail."""
        async with self._lock:
            self._snapshot = {
                zone_id: zone.model_copy(deep=True)
                for zone_id, zone in self._zones.items()
            }

    async def rollback_state(self) -> bool:
        """Restore zones from the last snapshot. Returns False if no snapshot exists."""
        async with self._lock:
            if self._snapshot is None:
                return False
            self._zones = self._snapshot
            self._snapshot = None
            self._alerts.append("[ROLLBACK] State restored to pre-LLM snapshot due to validation failure.")
            return True

    # ------------------------------------------------------------------
    # L2: Topology Gate — DAG Validation
    # ------------------------------------------------------------------

    async def validate_upstream_mitigation(self, bottleneck_id: str, proposed_zone_id: str) -> bool:
        """
        L2 Topology Gate: Verifies that the proposed mitigation zone is actually
        upstream of the bottleneck in the spatial DAG.

        Performs a BFS walk from the bottleneck's upstream_nodes to find the proposed zone.
        Returns True if the proposed zone is in the upstream path, False otherwise.
        """
        async with self._lock:
            if proposed_zone_id not in self._zones:
                self._alerts.append(
                    f"[L2 TOPOLOGY REJECTION] Zone '{proposed_zone_id}' does not exist in the DAG."
                )
                return False

            if bottleneck_id not in self._zones:
                self._alerts.append(
                    f"[L2 TOPOLOGY REJECTION] Bottleneck '{bottleneck_id}' does not exist in the DAG."
                )
                return False

            # BFS upstream from the bottleneck
            visited: set[str] = set()
            queue: list[str] = list(self._zones[bottleneck_id].upstream_nodes)

            while queue:
                current_id = queue.pop(0)
                if current_id in visited:
                    continue
                visited.add(current_id)

                if current_id == proposed_zone_id:
                    return True

                if current_id in self._zones:
                    queue.extend(self._zones[current_id].upstream_nodes)

            self._alerts.append(
                f"[L2 TOPOLOGY REJECTION] Zone '{proposed_zone_id}' is NOT upstream of "
                f"bottleneck '{bottleneck_id}'. Mitigation would be physically ineffective."
            )
            return False

    async def identify_bottleneck_zones(self) -> list[str]:
        """Returns zone IDs where occupancy exceeds 80% of max capacity."""
        async with self._lock:
            bottlenecks = []
            for zone_id, zone in self._zones.items():
                ratio = zone.current_occupancy / zone.max_capacity if zone.max_capacity > 0 else 0
                if ratio >= 0.80:
                    bottlenecks.append(zone_id)
            return bottlenecks

    # ------------------------------------------------------------------
    # Core State Operations
    # ------------------------------------------------------------------

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

    async def update_mitigation(self, zone_id: str, mitigation: str | None) -> bool:
        async with self._lock:
            if zone_id not in self._zones:
                self._alerts.append(
                    f"[MITIGATION REJECTED] Zone '{zone_id}' not found. Hallucinated zone ID from LLM."
                )
                return False

            self._zones[zone_id].mitigation_active = mitigation
            self._zones[zone_id].last_updated = datetime.utcnow().isoformat() + "Z"

            # L3: Initialize outcome monitoring for this mitigation
            if mitigation is not None:
                self._mitigation_tick_counter[zone_id] = 0
                # Capture baseline occupancy of downstream zones to measure effect
                downstream_baseline: dict[str, int] = {}
                for ds_id in self._zones[zone_id].downstream_nodes:
                    if ds_id in self._zones:
                        downstream_baseline[ds_id] = self._zones[ds_id].current_occupancy
                self._mitigation_baseline_occupancy[zone_id] = downstream_baseline
            else:
                # Mitigation cleared — stop monitoring
                self._mitigation_tick_counter.pop(zone_id, None)
                self._mitigation_baseline_occupancy.pop(zone_id, None)

            return True

    async def apply_bulk_update(self, new_state: list[dict[str, Any]]):
        async with self._lock:
            self._zones.clear()
            for row in new_state:
                zone = ZoneModel(**row)
                self._zones[zone.zone_id] = zone

    # ------------------------------------------------------------------
    # Alerts System — consumed by SSE stream
    # ------------------------------------------------------------------

    async def flush_alerts(self) -> list[str]:
        """Returns and clears all pending system alerts."""
        async with self._lock:
            alerts = list(self._alerts)
            self._alerts.clear()
            return alerts

    # ------------------------------------------------------------------
    # IoT Simulation + L3 Outcome Monitor
    # ------------------------------------------------------------------

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
            for _zone_id, zone in self._zones.items():
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

            # 3. L3 Outcome Monitor — check if active mitigations are actually working
            self._evaluate_mitigation_effectiveness()

    def _evaluate_mitigation_effectiveness(self):
        """
        L3 Outcome Monitor: For each zone with an active mitigation, check if
        downstream occupancy has decreased since the mitigation was applied.
        If not effective after MAX_INEFFECTIVE_TICKS, auto-clear and alert.

        MUST be called inside the lock context of simulate_iot_tick().
        """
        zones_to_clear: list[str] = []

        for zone_id, baseline_map in list(self._mitigation_baseline_occupancy.items()):
            if zone_id not in self._zones:
                zones_to_clear.append(zone_id)
                continue

            zone = self._zones[zone_id]
            if zone.mitigation_active is None:
                zones_to_clear.append(zone_id)
                continue

            # Check: has downstream occupancy improved?
            mitigation_effective = False
            for ds_id, baseline_occ in baseline_map.items():
                if ds_id in self._zones:
                    current_occ = self._zones[ds_id].current_occupancy
                    if current_occ < baseline_occ:
                        mitigation_effective = True
                        break

            if mitigation_effective:
                # Reset counter — mitigation is working
                self._mitigation_tick_counter[zone_id] = 0
            else:
                # Increment failure counter
                self._mitigation_tick_counter[zone_id] = self._mitigation_tick_counter.get(zone_id, 0) + 1

                if self._mitigation_tick_counter[zone_id] >= self.MAX_INEFFECTIVE_TICKS:
                    # Auto-clear ineffective mitigation
                    self._alerts.append(
                        f"[L3 OUTCOME MONITOR] Mitigation '{zone.mitigation_active}' at '{zone_id}' "
                        f"failed to reduce downstream occupancy after {self.MAX_INEFFECTIVE_TICKS} ticks. "
                        f"Auto-clearing and flagging for review."
                    )
                    zone.mitigation_active = None
                    zone.last_updated = datetime.utcnow().isoformat() + "Z"
                    zones_to_clear.append(zone_id)

        # Cleanup monitoring state for cleared mitigations
        for zone_id in zones_to_clear:
            self._mitigation_tick_counter.pop(zone_id, None)
            self._mitigation_baseline_occupancy.pop(zone_id, None)
