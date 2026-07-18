import asyncio
import logging
import random
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

NODE_TYPES = Literal["external", "turnstile", "corridor", "amenity", "seating"]


class ZoneModel(BaseModel):
    zone_id: str = Field(..., description="Unique ID of the stadium zone")
    node_type: NODE_TYPES = Field("corridor", description="Physical classification of the zone")
    current_occupancy: int = Field(..., ge=0, description="Current occupancy metric")
    max_capacity: int = Field(..., gt=0, description="Max safe capacity threshold")
    associated_gates: str = Field(..., description="Physical gates serving the zone")
    velocity: int = Field(0, description="Rate of change (fans/min)")
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z", description="ISO timestamp")

    # Physical dimensions for flow-rate calculations
    width_m: float = Field(10.0, description="Corridor width in meters")
    length_m: float = Field(50.0, description="Corridor length in meters")
    throughput_capacity_pph: int = Field(2000, description="Maximum throughput (people per hour)")

    # Topological mapping
    upstream_nodes: list[str] = Field(default_factory=list, description="IDs of zones that flow into this zone")
    downstream_nodes: list[str] = Field(default_factory=list, description="IDs of zones this zone flows into")

    # AI state
    mitigation_active: str | None = Field(None, description="Active mitigation")

    # Predetermined action items — populated by deterministic engine
    todo_list: list[str] = Field(default_factory=list, description="Auto-populated action items based on thresholds")


class StadiumStateManager:
    """
    Thread-safe Singleton state manager operating on a 15-node FIFA stadium DAG.
    Supports flow-rate anomaly detection and predetermined TODO suggestions.
    """
    _instance = None
    MAX_INEFFECTIVE_TICKS = 3
    FLOW_RATE_ANOMALY_THRESHOLD = 0.25

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self._lock = asyncio.Lock()
        self._zones: dict[str, ZoneModel] = {
            # --- External Layer ---
            "Parking A": ZoneModel(
                zone_id="Parking A", node_type="external", current_occupancy=2000, max_capacity=15000,
                associated_gates="Lot A", downstream_nodes=["North Plaza"],
                width_m=100.0, length_m=80.0, throughput_capacity_pph=5000
            ),
            "Parking B": ZoneModel(
                zone_id="Parking B", node_type="external", current_occupancy=1800, max_capacity=15000,
                associated_gates="Lot B", downstream_nodes=["South Plaza"],
                width_m=100.0, length_m=80.0, throughput_capacity_pph=5000
            ),
            # --- Outer Perimeter (Plazas) ---
            "North Plaza": ZoneModel(
                zone_id="North Plaza", node_type="external", current_occupancy=1200, max_capacity=8000,
                associated_gates="Plaza N", upstream_nodes=["Parking A"], downstream_nodes=["Gate A", "Gate B"],
                width_m=60.0, length_m=40.0, throughput_capacity_pph=4000
            ),
            "South Plaza": ZoneModel(
                zone_id="South Plaza", node_type="external", current_occupancy=1000, max_capacity=8000,
                associated_gates="Plaza S", upstream_nodes=["Parking B"], downstream_nodes=["Gate C", "Gate D"],
                width_m=60.0, length_m=40.0, throughput_capacity_pph=4000
            ),
            # --- Turnstiles ---
            "Gate A": ZoneModel(
                zone_id="Gate A", node_type="turnstile", current_occupancy=80, max_capacity=500,
                associated_gates="Gate A", upstream_nodes=["North Plaza"], downstream_nodes=["North Concourse"],
                width_m=15.0, length_m=5.0, throughput_capacity_pph=1200
            ),
            "Gate B": ZoneModel(
                zone_id="Gate B", node_type="turnstile", current_occupancy=120, max_capacity=600,
                associated_gates="Gate B", upstream_nodes=["North Plaza"], downstream_nodes=["Main Concourse"],
                width_m=20.0, length_m=5.0, throughput_capacity_pph=1800
            ),
            "Gate C": ZoneModel(
                zone_id="Gate C", node_type="turnstile", current_occupancy=100, max_capacity=600,
                associated_gates="Gate C", upstream_nodes=["South Plaza"], downstream_nodes=["Main Concourse"],
                width_m=20.0, length_m=5.0, throughput_capacity_pph=1800
            ),
            "Gate D": ZoneModel(
                zone_id="Gate D", node_type="turnstile", current_occupancy=60, max_capacity=500,
                associated_gates="Gate D", upstream_nodes=["South Plaza"], downstream_nodes=["South Concourse"],
                width_m=15.0, length_m=5.0, throughput_capacity_pph=1200
            ),
            # --- Corridors ---
            "North Concourse": ZoneModel(
                zone_id="North Concourse", node_type="corridor", current_occupancy=800, max_capacity=4000,
                associated_gates="Internal N", upstream_nodes=["Gate A"], downstream_nodes=["Food Court", "Bowl NW"],
                width_m=8.0, length_m=120.0, throughput_capacity_pph=2400
            ),
            "Main Concourse": ZoneModel(
                zone_id="Main Concourse", node_type="corridor", current_occupancy=3000, max_capacity=12000,
                associated_gates="Central", upstream_nodes=["Gate B", "Gate C"],
                downstream_nodes=["Food Court", "Medical Bay", "Restroom Zone", "Bowl NE", "Bowl SE"],
                width_m=12.0, length_m=200.0, throughput_capacity_pph=6000
            ),
            "South Concourse": ZoneModel(
                zone_id="South Concourse", node_type="corridor", current_occupancy=600, max_capacity=4000,
                associated_gates="Internal S", upstream_nodes=["Gate D"], downstream_nodes=["Restroom Zone", "Bowl SW"],
                width_m=8.0, length_m=120.0, throughput_capacity_pph=2400
            ),
            # --- Amenities ---
            "Food Court": ZoneModel(
                zone_id="Food Court", node_type="amenity", current_occupancy=400, max_capacity=2000,
                associated_gates="F&B Area", upstream_nodes=["North Concourse", "Main Concourse"], downstream_nodes=[],
                width_m=30.0, length_m=20.0, throughput_capacity_pph=800
            ),
            "Medical Bay": ZoneModel(
                zone_id="Medical Bay", node_type="amenity", current_occupancy=5, max_capacity=50,
                associated_gates="Medical", upstream_nodes=["Main Concourse"], downstream_nodes=[],
                width_m=10.0, length_m=10.0, throughput_capacity_pph=200
            ),
            "Restroom Zone": ZoneModel(
                zone_id="Restroom Zone", node_type="amenity", current_occupancy=80, max_capacity=300,
                associated_gates="Facilities", upstream_nodes=["Main Concourse", "South Concourse"], downstream_nodes=[],
                width_m=15.0, length_m=10.0, throughput_capacity_pph=600
            ),
            # --- Bowl Sections ---
            "Bowl NW": ZoneModel(
                zone_id="Bowl NW", node_type="seating", current_occupancy=8000, max_capacity=15000,
                associated_gates="Section 100-109", upstream_nodes=["North Concourse"], downstream_nodes=[],
                width_m=50.0, length_m=30.0, throughput_capacity_pph=3000
            ),
            "Bowl NE": ZoneModel(
                zone_id="Bowl NE", node_type="seating", current_occupancy=9000, max_capacity=15000,
                associated_gates="Section 110-119", upstream_nodes=["Main Concourse"], downstream_nodes=[],
                width_m=50.0, length_m=30.0, throughput_capacity_pph=3000
            ),
            "Bowl SW": ZoneModel(
                zone_id="Bowl SW", node_type="seating", current_occupancy=7000, max_capacity=15000,
                associated_gates="Section 200-209", upstream_nodes=["South Concourse"], downstream_nodes=[],
                width_m=50.0, length_m=30.0, throughput_capacity_pph=3000
            ),
            "Bowl SE": ZoneModel(
                zone_id="Bowl SE", node_type="seating", current_occupancy=8500, max_capacity=15000,
                associated_gates="Section 210-219", upstream_nodes=["Main Concourse"], downstream_nodes=[],
                width_m=50.0, length_m=30.0, throughput_capacity_pph=3000
            ),
        }
        self._snapshot: dict[str, ZoneModel] | None = None
        self._mitigation_tick_counter: dict[str, int] = {}
        self._mitigation_baseline_occupancy: dict[str, dict[str, int]] = {}
        self._alerts: list[str] = []
        self._anomaly_queue: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Anomaly Queue Management
    # ------------------------------------------------------------------

    async def get_anomaly_queue(self) -> list[dict[str, Any]]:
        async with self._lock:
            return list(self._anomaly_queue)

    async def flush_anomaly_queue(self) -> list[dict[str, Any]]:
        async with self._lock:
            anomalies = list(self._anomaly_queue)
            self._anomaly_queue.clear()
            return anomalies

    async def append_anomaly(self, anomaly: dict[str, Any]):
        async with self._lock:
            self._anomaly_queue.append(anomaly)

    # ------------------------------------------------------------------
    # State Snapshot & Rollback
    # ------------------------------------------------------------------

    async def snapshot_state(self):
        async with self._lock:
            self._snapshot = {zid: z.model_copy(deep=True) for zid, z in self._zones.items()}

    async def rollback_state(self) -> bool:
        async with self._lock:
            if self._snapshot is None:
                return False
            self._zones = self._snapshot
            self._snapshot = None
            self._alerts.append("[ROLLBACK] State restored to pre-LLM snapshot.")
            return True

    # ------------------------------------------------------------------
    # L2: Topology Gate — DAG Validation
    # ------------------------------------------------------------------

    async def validate_upstream_mitigation(self, bottleneck_id: str, proposed_zone_id: str) -> bool:
        async with self._lock:
            if proposed_zone_id not in self._zones or bottleneck_id not in self._zones:
                return False
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
            return False

    async def identify_bottleneck_zones(self) -> list[str]:
        async with self._lock:
            return [
                zid for zid, z in self._zones.items()
                if (z.current_occupancy / z.max_capacity if z.max_capacity > 0 else 0) >= 0.80
            ]

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
                return False
            self._zones[zone_id].mitigation_active = mitigation
            self._zones[zone_id].last_updated = datetime.utcnow().isoformat() + "Z"
            if mitigation is not None:
                self._mitigation_tick_counter[zone_id] = 0
                downstream_baseline: dict[str, int] = {}
                for ds_id in self._zones[zone_id].downstream_nodes:
                    if ds_id in self._zones:
                        downstream_baseline[ds_id] = self._zones[ds_id].current_occupancy
                self._mitigation_baseline_occupancy[zone_id] = downstream_baseline
            else:
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
    # Alerts System
    # ------------------------------------------------------------------

    async def flush_alerts(self) -> list[str]:
        async with self._lock:
            alerts = list(self._alerts)
            self._alerts.clear()
            return alerts

    # ------------------------------------------------------------------
    # IoT Simulation + TODO Auto-Population + Flow-Rate Anomaly Detection
    # ------------------------------------------------------------------

    async def simulate_iot_tick(self):
        async with self._lock:
            # 1. Add influx to external nodes (parking lots)
            for ext_id in ["Parking A", "Parking B"]:
                if ext_id in self._zones:
                    ext = self._zones[ext_id]
                    addition = random.randint(30, 100)
                    ext.current_occupancy = min(ext.max_capacity, ext.current_occupancy + addition)
                    ext.velocity = addition * 8
                    ext.last_updated = datetime.utcnow().isoformat() + "Z"

            # 2. Propagate traffic downstream through DAG
            for _zid, zone in self._zones.items():
                if zone.upstream_nodes:
                    total_influx = 0
                    for up_id in zone.upstream_nodes:
                        if up_id not in self._zones:
                            continue
                        up_zone = self._zones[up_id]
                        # Transfer rate varies by node type
                        if up_zone.node_type == "external":
                            transfer = int(up_zone.current_occupancy * 0.05)
                        elif up_zone.node_type == "turnstile":
                            transfer = int(up_zone.current_occupancy * 0.30)
                        else:
                            transfer = int(up_zone.current_occupancy * 0.08)

                        if up_zone.mitigation_active:
                            transfer = int(transfer * 0.1)

                        up_zone.current_occupancy = max(0, up_zone.current_occupancy - transfer)
                        total_influx += transfer

                    local_addition = random.randint(5, 20)
                    new_occ = min(zone.max_capacity, zone.current_occupancy + total_influx + local_addition)
                    actual_addition = new_occ - zone.current_occupancy
                    zone.current_occupancy = new_occ
                    zone.velocity = actual_addition * 5
                    zone.last_updated = datetime.utcnow().isoformat() + "Z"

            # 3. Auto-populate TODO lists based on thresholds
            self._populate_todo_lists()

            # 4. L3 Outcome Monitor
            self._evaluate_mitigation_effectiveness()

            # 5. Flow-Rate Anomaly Detection
            self._detect_flow_rate_anomalies()

    def _populate_todo_lists(self):
        """Auto-populate predetermined action items on each node based on occupancy thresholds."""
        from src.domain.deterministic_rules import get_predetermined_suggestions

        for _zid, zone in self._zones.items():
            ratio = zone.current_occupancy / zone.max_capacity if zone.max_capacity > 0 else 0
            pct = ratio * 100
            zone.todo_list = get_predetermined_suggestions(zone.node_type, pct)

    def _detect_flow_rate_anomalies(self):
        for zone_id, zone in self._zones.items():
            if zone.throughput_capacity_pph <= 0:
                continue
            actual_hourly_rate = abs(zone.velocity) * 900
            flow_ratio = actual_hourly_rate / zone.throughput_capacity_pph
            if flow_ratio >= self.FLOW_RATE_ANOMALY_THRESHOLD:
                continue
            upstream_congested = any(
                self._zones[up_id].current_occupancy / self._zones[up_id].max_capacity >= 0.60
                for up_id in zone.upstream_nodes if up_id in self._zones
            )
            if not upstream_congested:
                continue
            already_queued = any(
                a.get("zone_id") == zone_id and a.get("type") == "FLOW_MISMATCH"
                for a in self._anomaly_queue
            )
            if already_queued:
                continue
            self._anomaly_queue.append({
                "type": "FLOW_MISMATCH", "zone_id": zone_id,
                "actual_flow_pph": actual_hourly_rate,
                "capacity_pph": zone.throughput_capacity_pph,
                "flow_ratio": round(flow_ratio, 2),
                "width_m": zone.width_m, "length_m": zone.length_m,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            self._alerts.append(
                f"[FLOW ANOMALY] '{zone_id}' throughput at {actual_hourly_rate} pph "
                f"vs capacity {zone.throughput_capacity_pph} pph."
            )

    def _evaluate_mitigation_effectiveness(self):
        zones_to_clear: list[str] = []
        for zone_id, baseline_map in list(self._mitigation_baseline_occupancy.items()):
            if zone_id not in self._zones:
                zones_to_clear.append(zone_id)
                continue
            zone = self._zones[zone_id]
            if zone.mitigation_active is None:
                zones_to_clear.append(zone_id)
                continue
            mitigation_effective = any(
                self._zones[ds_id].current_occupancy < baseline_occ
                for ds_id, baseline_occ in baseline_map.items() if ds_id in self._zones
            )
            if mitigation_effective:
                self._mitigation_tick_counter[zone_id] = 0
            else:
                self._mitigation_tick_counter[zone_id] = self._mitigation_tick_counter.get(zone_id, 0) + 1
                if self._mitigation_tick_counter[zone_id] >= self.MAX_INEFFECTIVE_TICKS:
                    self._alerts.append(
                        f"[L3 OUTCOME MONITOR] Mitigation '{zone.mitigation_active}' at '{zone_id}' "
                        f"ineffective after {self.MAX_INEFFECTIVE_TICKS} ticks. Auto-clearing."
                    )
                    zone.mitigation_active = None
                    zone.last_updated = datetime.utcnow().isoformat() + "Z"
                    zones_to_clear.append(zone_id)
        for zone_id in zones_to_clear:
            self._mitigation_tick_counter.pop(zone_id, None)
            self._mitigation_baseline_occupancy.pop(zone_id, None)
