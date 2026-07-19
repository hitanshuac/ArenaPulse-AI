import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from src.domain.models import ZoneModel
from src.domain.physics import build_gravity_map, simulate_physics_tick

logger = logging.getLogger(__name__)


class StadiumStateManager:
    """
    Thread-safe Singleton state manager operating on a 15-node FIFA stadium Bidirectional Flow Graph.
    Delegates physics calculations to pure physics engine functions.
    """

    _instance = None
    MAX_INEFFECTIVE_TICKS = 3
    FLOW_RATE_ANOMALY_THRESHOLD = 0.10

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self._lock = asyncio.Lock()
        self.current_phase = "INGRESS"  # Phases: INGRESS, MATCH, EGRESS
        self.match_minute = 0
        self.match_running = False

        self._zones: dict[str, ZoneModel] = {
            # --- External Layer ---
            "Parking A": ZoneModel(
                zone_id="Parking A",
                node_type="external",
                current_occupancy=2000,
                max_capacity=40000,
                associated_gates="Lot A",
                connected_nodes=["North Plaza"],
                width_m=200.0,
                length_m=200.0,
                throughput_capacity_pph=25000,
            ),
            "Parking B": ZoneModel(
                zone_id="Parking B",
                node_type="external",
                current_occupancy=1800,
                max_capacity=40000,
                associated_gates="Lot B",
                connected_nodes=["South Plaza"],
                width_m=200.0,
                length_m=200.0,
                throughput_capacity_pph=25000,
            ),
            # --- Outer Perimeter (Plazas) ---
            "North Plaza": ZoneModel(
                zone_id="North Plaza",
                node_type="external",
                current_occupancy=1200,
                max_capacity=20000,
                associated_gates="Plaza N",
                connected_nodes=["Parking A", "Gate A", "Gate B"],
                width_m=100.0,
                length_m=50.0,
                throughput_capacity_pph=25000,
            ),
            "South Plaza": ZoneModel(
                zone_id="South Plaza",
                node_type="external",
                current_occupancy=1000,
                max_capacity=20000,
                associated_gates="Plaza S",
                connected_nodes=["Parking B", "Gate C", "Gate D"],
                width_m=100.0,
                length_m=50.0,
                throughput_capacity_pph=25000,
            ),
            # --- Turnstiles ---
            "Gate A": ZoneModel(
                zone_id="Gate A",
                node_type="turnstile",
                current_occupancy=80,
                max_capacity=2000,
                associated_gates="Gate A",
                connected_nodes=["North Plaza", "North Concourse"],
                width_m=25.0,
                length_m=20.0,
                throughput_capacity_pph=10000,
            ),
            "Gate B": ZoneModel(
                zone_id="Gate B",
                node_type="turnstile",
                current_occupancy=120,
                max_capacity=2000,
                associated_gates="Gate B",
                connected_nodes=["North Plaza", "Main Concourse"],
                width_m=25.0,
                length_m=20.0,
                throughput_capacity_pph=10000,
            ),
            "Gate C": ZoneModel(
                zone_id="Gate C",
                node_type="turnstile",
                current_occupancy=100,
                max_capacity=2000,
                associated_gates="Gate C",
                connected_nodes=["South Plaza", "Main Concourse"],
                width_m=25.0,
                length_m=20.0,
                throughput_capacity_pph=10000,
            ),
            "Gate D": ZoneModel(
                zone_id="Gate D",
                node_type="turnstile",
                current_occupancy=60,
                max_capacity=2000,
                associated_gates="Gate D",
                connected_nodes=["South Plaza", "South Concourse"],
                width_m=25.0,
                length_m=20.0,
                throughput_capacity_pph=10000,
            ),
            # --- Corridors ---
            "North Concourse": ZoneModel(
                zone_id="North Concourse",
                node_type="corridor",
                current_occupancy=800,
                max_capacity=10000,
                associated_gates="Internal N",
                connected_nodes=["Gate A", "Food Court", "Bowl NW"],
                width_m=20.0,
                length_m=125.0,
                throughput_capacity_pph=15000,
            ),
            "Main Concourse": ZoneModel(
                zone_id="Main Concourse",
                node_type="corridor",
                current_occupancy=3000,
                max_capacity=30000,
                associated_gates="Central",
                connected_nodes=[
                    "Gate B",
                    "Gate C",
                    "Food Court",
                    "Medical Bay",
                    "Restroom Zone",
                    "Bowl NE",
                    "Bowl SE",
                ],
                width_m=30.0,
                length_m=250.0,
                throughput_capacity_pph=30000,
            ),
            "South Concourse": ZoneModel(
                zone_id="South Concourse",
                node_type="corridor",
                current_occupancy=600,
                max_capacity=10000,
                associated_gates="Internal S",
                connected_nodes=["Gate D", "Restroom Zone", "Bowl SW"],
                width_m=20.0,
                length_m=125.0,
                throughput_capacity_pph=15000,
            ),
            # --- Amenities ---
            "Food Court": ZoneModel(
                zone_id="Food Court",
                node_type="amenity",
                current_occupancy=400,
                max_capacity=5000,
                associated_gates="F&B Area",
                connected_nodes=["North Concourse", "Main Concourse"],
                width_m=50.0,
                length_m=25.0,
                throughput_capacity_pph=5000,
            ),
            "Medical Bay": ZoneModel(
                zone_id="Medical Bay",
                node_type="amenity",
                current_occupancy=5,
                max_capacity=200,
                associated_gates="Medical",
                connected_nodes=["Main Concourse"],
                width_m=10.0,
                length_m=5.0,
                throughput_capacity_pph=500,
            ),
            "Restroom Zone": ZoneModel(
                zone_id="Restroom Zone",
                node_type="amenity",
                current_occupancy=80,
                max_capacity=2000,
                associated_gates="Facilities",
                connected_nodes=["Main Concourse", "South Concourse"],
                width_m=25.0,
                length_m=20.0,
                throughput_capacity_pph=2500,
            ),
            # --- Bowl Sections ---
            "Bowl NW": ZoneModel(
                zone_id="Bowl NW",
                node_type="seating",
                current_occupancy=8000,
                max_capacity=15000,
                associated_gates="Section 100-109",
                connected_nodes=["North Concourse"],
                width_m=100.0,
                length_m=50.0,
                throughput_capacity_pph=10000,
            ),
            "Bowl NE": ZoneModel(
                zone_id="Bowl NE",
                node_type="seating",
                current_occupancy=9000,
                max_capacity=15000,
                associated_gates="Section 110-119",
                connected_nodes=["Main Concourse"],
                width_m=100.0,
                length_m=50.0,
                throughput_capacity_pph=10000,
            ),
            "Bowl SW": ZoneModel(
                zone_id="Bowl SW",
                node_type="seating",
                current_occupancy=7000,
                max_capacity=15000,
                associated_gates="Section 200-209",
                connected_nodes=["South Concourse"],
                width_m=100.0,
                length_m=50.0,
                throughput_capacity_pph=10000,
            ),
            "Bowl SE": ZoneModel(
                zone_id="Bowl SE",
                node_type="seating",
                current_occupancy=8500,
                max_capacity=15000,
                associated_gates="Section 210-219",
                connected_nodes=["Main Concourse"],
                width_m=100.0,
                length_m=50.0,
                throughput_capacity_pph=10000,
            ),
        }

        # Physics Fix 1: Calculate max_capacity dynamically from physical dimensions
        # Density: 4 persons per square meter for standing/flowing crowd.
        for zid, z in self._zones.items():
            if z.node_type not in ["seating", "external"] or "Plaza" in zid:
                z.max_capacity = int(z.width_m * z.length_m * 4)

        self._snapshot: dict[str, ZoneModel] | None = None
        self._mitigation_tick_counter: dict[str, int] = {}
        self._mitigation_baseline_occupancy: dict[str, dict[str, int]] = {}
        self._alerts: list[str] = []
        self._anomaly_queue: list[dict[str, Any]] = []
        self._gravity_map = build_gravity_map(self._zones)

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
    # Core State Operations
    # ------------------------------------------------------------------

    async def get_all_zones(self) -> list[dict[str, Any]]:
        async with self._lock:
            return [z.model_dump() for z in self._zones.values()]

    async def get_system_metadata(self) -> dict[str, Any]:
        async with self._lock:
            return {
                "current_phase": self.current_phase,
                "match_minute": self.match_minute,
                "match_running": self.match_running,
            }

    async def set_phase(self, new_phase: str):
        async with self._lock:
            if new_phase in ["INGRESS", "MATCH", "EGRESS"]:
                self.current_phase = new_phase
                # Sync match clock to phase position
                if new_phase == "INGRESS":
                    self.match_minute = 0
                elif new_phase == "MATCH":
                    self.match_minute = 45
                elif new_phase == "EGRESS":
                    self.match_minute = 90
                self.match_running = True
                self._alerts.append(
                    f"[MIN {self.match_minute}] [PHASE SHIFT] Stadium phase transitioned to {new_phase}."
                )

    async def update_zone_occupancy(self, zone_id: str, new_occupancy: int) -> bool:
        async with self._lock:
            if zone_id in self._zones:
                self._zones[zone_id].current_occupancy = max(0, new_occupancy)
                self._zones[zone_id].last_updated = datetime.now(UTC).isoformat() + "Z"
                return True
            return False

    async def update_mitigation(self, zone_id: str, mitigation: str | None) -> bool:
        async with self._lock:
            if zone_id not in self._zones:
                return False
            self._zones[zone_id].mitigation_active = mitigation
            self._zones[zone_id].last_updated = datetime.now(UTC).isoformat() + "Z"
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
    # Tick Update Delegation
    # ------------------------------------------------------------------

    async def simulate_iot_tick(self):
        async with self._lock:
            # Advance match clock if running
            if self.match_running:
                self.match_minute += 1
                # Auto-phase transitions based on match minute
                if self.match_minute == 45 and self.current_phase == "INGRESS":
                    self.current_phase = "MATCH"
                    self._alerts.append(
                        f"[MIN {self.match_minute}] [AUTO-PHASE] Kickoff! Phase → MATCH. Crowd settled in bowls."
                    )
                elif self.match_minute == 90 and self.current_phase == "MATCH":
                    self.current_phase = "EGRESS"
                    self._alerts.append(
                        f"[MIN {self.match_minute}] [AUTO-PHASE] Full time! Phase → EGRESS. Mass exit initiated."
                    )
                elif self.match_minute >= 120:
                    self.match_running = False
                    self._alerts.append(
                        f"[MIN {self.match_minute}] [COMPLETE] Stadium evacuation simulation complete."
                    )

            simulate_physics_tick(
                self._zones,
                self.current_phase,
                self._gravity_map,
                self._anomaly_queue,
                self._alerts,
                self.FLOW_RATE_ANOMALY_THRESHOLD,
            )
