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
    
    # Bidirectional Flow Metrics
    inflow_rate: int = Field(0, description="Rate of fans entering (fans/min)")
    outflow_rate: int = Field(0, description="Rate of fans exiting (fans/min)")
    net_velocity: int = Field(0, description="Net rate of change (inflow - outflow)")
    
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z", description="ISO timestamp")

    # Physical dimensions for flow-rate calculations
    width_m: float = Field(10.0, description="Corridor width in meters")
    length_m: float = Field(50.0, description="Corridor length in meters")
    throughput_capacity_pph: int = Field(2000, description="Maximum throughput (people per hour)")

    # topological mapping (Bidirectional)
    connected_nodes: list[str] = Field(default_factory=list, description="IDs of adjacent zones for bidirectional flow")

    # AI state
    mitigation_active: str | None = Field(None, description="Active mitigation")

    # Predetermined action items
    todo_list: list[str] = Field(default_factory=list, description="Auto-populated action items based on thresholds")


class StadiumStateManager:
    """
    Thread-safe Singleton state manager operating on a 15-node FIFA stadium Bidirectional Flow Graph.
    Uses Phase-Gravity to determine crowd directional vectors.
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
        self.current_phase = "INGRESS"  # Phases: INGRESS, MATCH, EGRESS

        self._zones: dict[str, ZoneModel] = {
            # --- External Layer ---
            "Parking A": ZoneModel(
                zone_id="Parking A", node_type="external", current_occupancy=2000, max_capacity=15000,
                associated_gates="Lot A", connected_nodes=["North Plaza"],
                width_m=100.0, length_m=80.0, throughput_capacity_pph=5000
            ),
            "Parking B": ZoneModel(
                zone_id="Parking B", node_type="external", current_occupancy=1800, max_capacity=15000,
                associated_gates="Lot B", connected_nodes=["South Plaza"],
                width_m=100.0, length_m=80.0, throughput_capacity_pph=5000
            ),
            # --- Outer Perimeter (Plazas) ---
            "North Plaza": ZoneModel(
                zone_id="North Plaza", node_type="external", current_occupancy=1200, max_capacity=8000,
                associated_gates="Plaza N", connected_nodes=["Parking A", "Gate A", "Gate B"],
                width_m=60.0, length_m=40.0, throughput_capacity_pph=4000
            ),
            "South Plaza": ZoneModel(
                zone_id="South Plaza", node_type="external", current_occupancy=1000, max_capacity=8000,
                associated_gates="Plaza S", connected_nodes=["Parking B", "Gate C", "Gate D"],
                width_m=60.0, length_m=40.0, throughput_capacity_pph=4000
            ),
            # --- Turnstiles ---
            "Gate A": ZoneModel(
                zone_id="Gate A", node_type="turnstile", current_occupancy=80, max_capacity=500,
                associated_gates="Gate A", connected_nodes=["North Plaza", "North Concourse"],
                width_m=15.0, length_m=5.0, throughput_capacity_pph=1200
            ),
            "Gate B": ZoneModel(
                zone_id="Gate B", node_type="turnstile", current_occupancy=120, max_capacity=600,
                associated_gates="Gate B", connected_nodes=["North Plaza", "Main Concourse"],
                width_m=20.0, length_m=5.0, throughput_capacity_pph=1800
            ),
            "Gate C": ZoneModel(
                zone_id="Gate C", node_type="turnstile", current_occupancy=100, max_capacity=600,
                associated_gates="Gate C", connected_nodes=["South Plaza", "Main Concourse"],
                width_m=20.0, length_m=5.0, throughput_capacity_pph=1800
            ),
            "Gate D": ZoneModel(
                zone_id="Gate D", node_type="turnstile", current_occupancy=60, max_capacity=500,
                associated_gates="Gate D", connected_nodes=["South Plaza", "South Concourse"],
                width_m=15.0, length_m=5.0, throughput_capacity_pph=1200
            ),
            # --- Corridors ---
            "North Concourse": ZoneModel(
                zone_id="North Concourse", node_type="corridor", current_occupancy=800, max_capacity=10000,
                associated_gates="Internal N", connected_nodes=["Gate A", "Food Court", "Bowl NW"],
                width_m=8.0, length_m=120.0, throughput_capacity_pph=2400
            ),
            "Main Concourse": ZoneModel(
                zone_id="Main Concourse", node_type="corridor", current_occupancy=3000, max_capacity=30000,
                associated_gates="Central", connected_nodes=["Gate B", "Gate C", "Food Court", "Medical Bay", "Restroom Zone", "Bowl NE", "Bowl SE"],
                width_m=12.0, length_m=200.0, throughput_capacity_pph=6000
            ),
            "South Concourse": ZoneModel(
                zone_id="South Concourse", node_type="corridor", current_occupancy=600, max_capacity=10000,
                associated_gates="Internal S", connected_nodes=["Gate D", "Restroom Zone", "Bowl SW"],
                width_m=8.0, length_m=120.0, throughput_capacity_pph=2400
            ),
            # --- Amenities ---
            "Food Court": ZoneModel(
                zone_id="Food Court", node_type="amenity", current_occupancy=400, max_capacity=10000,
                associated_gates="F&B Area", connected_nodes=["North Concourse", "Main Concourse"],
                width_m=30.0, length_m=20.0, throughput_capacity_pph=800
            ),
            "Medical Bay": ZoneModel(
                zone_id="Medical Bay", node_type="amenity", current_occupancy=5, max_capacity=100,
                associated_gates="Medical", connected_nodes=["Main Concourse"],
                width_m=10.0, length_m=10.0, throughput_capacity_pph=200
            ),
            "Restroom Zone": ZoneModel(
                zone_id="Restroom Zone", node_type="amenity", current_occupancy=80, max_capacity=5000,
                associated_gates="Facilities", connected_nodes=["Main Concourse", "South Concourse"],
                width_m=15.0, length_m=10.0, throughput_capacity_pph=600
            ),
            # --- Bowl Sections ---
            "Bowl NW": ZoneModel(
                zone_id="Bowl NW", node_type="seating", current_occupancy=8000, max_capacity=15000,
                associated_gates="Section 100-109", connected_nodes=["North Concourse"],
                width_m=50.0, length_m=30.0, throughput_capacity_pph=3000
            ),
            "Bowl NE": ZoneModel(
                zone_id="Bowl NE", node_type="seating", current_occupancy=9000, max_capacity=15000,
                associated_gates="Section 110-119", connected_nodes=["Main Concourse"],
                width_m=50.0, length_m=30.0, throughput_capacity_pph=3000
            ),
            "Bowl SW": ZoneModel(
                zone_id="Bowl SW", node_type="seating", current_occupancy=7000, max_capacity=15000,
                associated_gates="Section 200-209", connected_nodes=["South Concourse"],
                width_m=50.0, length_m=30.0, throughput_capacity_pph=3000
            ),
            "Bowl SE": ZoneModel(
                zone_id="Bowl SE", node_type="seating", current_occupancy=8500, max_capacity=15000,
                associated_gates="Section 210-219", connected_nodes=["Main Concourse"],
                width_m=50.0, length_m=30.0, throughput_capacity_pph=3000
            ),
        }
        self._snapshot: dict[str, ZoneModel] | None = None
        self._mitigation_tick_counter: dict[str, int] = {}
        self._mitigation_baseline_occupancy: dict[str, dict[str, int]] = {}
        self._alerts: list[str] = []
        self._anomaly_queue: list[dict[str, Any]] = []
        self._gravity_map = self._build_gravity_map()

    def _build_gravity_map(self):
        """Precomputes distances to 'sinks' for fluid dynamic routing."""
        # Gravity levels: Seating=0, Corridors=1, Turnstiles=2, Plazas=3.5, External=4
        gmap = {}
        for zid, z in self._zones.items():
            if z.node_type == "seating": gmap[zid] = 0
            elif z.node_type == "amenity": gmap[zid] = 1
            elif z.node_type == "corridor": gmap[zid] = 2
            elif z.node_type == "turnstile": gmap[zid] = 3
            elif z.node_type == "external": 
                if "Plaza" in zid:
                    gmap[zid] = 3.5
                else:
                    gmap[zid] = 4
        return gmap

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
            return {"current_phase": self.current_phase}

    async def set_phase(self, new_phase: str):
        async with self._lock:
            if new_phase in ["INGRESS", "MATCH", "EGRESS"]:
                self.current_phase = new_phase
                self._alerts.append(f"[PHASE SHIFT] Stadium phase transitioned to {new_phase}.")

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
            # Mitigation effectiveness tracking is disabled for simplicity in Bidirectional model, 
            # as determining "downstream" requires calculating real-time fluid diffusion.
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
    # Phase-Gravity Fluid Dynamics Simulation
    # ------------------------------------------------------------------

    async def simulate_iot_tick(self):
        async with self._lock:
            # 1. External Additions/Subtractions based on phase
            if self.current_phase == "INGRESS":
                for ext_id in ["Parking A", "Parking B"]:
                    if ext_id in self._zones:
                        ext = self._zones[ext_id]
                        add = random.randint(50, 150)
                        ext.current_occupancy = min(ext.max_capacity, ext.current_occupancy + add)
                        ext.inflow_rate += add
            elif self.current_phase == "EGRESS":
                # Drain people out of the system from the Parking Lots
                for ext_id in ["Parking A", "Parking B"]:
                    if ext_id in self._zones:
                        ext = self._zones[ext_id]
                        sub = random.randint(100, 300)
                        if ext.current_occupancy >= sub:
                            ext.current_occupancy -= sub
                            ext.outflow_rate += sub

            # Reset tick velocities
            for z in self._zones.values():
                # Decay to simulate rolling average
                z.inflow_rate = int(z.inflow_rate * 0.5)
                z.outflow_rate = int(z.outflow_rate * 0.5)

            # 2. Simulate Fluid Dynamics (Phase-Gravity)
            # People move from higher gravity (source) to lower gravity (sink)
            # Ingress: External(4) -> Seating(0)
            # Egress: Seating(0) -> External(4)
            # Match: Random walk between Amenity(1) and Seating(0)
            
            transfers = [] # (from_id, to_id, amount)
            
            for zone_id, zone in self._zones.items():
                if not zone.connected_nodes or zone.current_occupancy <= 0:
                    continue
                
                for neighbor_id in zone.connected_nodes:
                    if neighbor_id not in self._zones:
                        continue
                    
                    my_g = self._gravity_map[zone_id]
                    nbr_g = self._gravity_map[neighbor_id]
                    
                    # Calculate flow potential based on phase
                    flow_amount = 0
                    
                    neighbor_zone = self._zones[neighbor_id]
                    if neighbor_zone.node_type == "amenity":
                        # Amenities absorb a tiny trickle from corridors
                        if (neighbor_zone.current_occupancy / neighbor_zone.max_capacity) < 0.7:
                            flow_amount = int(zone.current_occupancy * 0.01)
                    elif zone.node_type == "amenity":
                        # Amenities constantly drain back into corridors to avoid black holes
                        flow_amount = int(zone.current_occupancy * 0.15)
                    else:
                        if self.current_phase == "INGRESS":
                            if my_g > nbr_g: # e.g. External(4) to Turnstile(3)
                                flow_amount = int(zone.current_occupancy * 0.1)
                        elif self.current_phase == "EGRESS":
                            if my_g < nbr_g: # e.g. Seating(0) to Corridor(2)
                                flow_amount = int(zone.current_occupancy * 0.15)
                        elif self.current_phase == "MATCH":
                            # Bidirectional milling between adjacent nodes
                            # High occupancy naturally diffuses
                            ratio_diff = (zone.current_occupancy / zone.max_capacity) - (neighbor_zone.current_occupancy / neighbor_zone.max_capacity)
                            if ratio_diff > 0.1:
                                flow_amount = int(zone.current_occupancy * 0.02)
                    
                    if flow_amount > 0:
                        if zone.mitigation_active:
                            flow_amount = int(flow_amount * 0.2) # Mitigation throttles outflow
                        transfers.append((zone_id, neighbor_id, flow_amount))

            # Apply transfers
            for source, sink, amount in transfers:
                if self._zones[source].current_occupancy >= amount:
                    self._zones[source].current_occupancy -= amount
                    self._zones[source].outflow_rate += amount
                    
                    self._zones[sink].current_occupancy += amount
                    self._zones[sink].inflow_rate += amount

            # Update net velocities
            for zone in self._zones.values():
                # People per minute scaling (tick is ~5s but simulated as faster)
                zone.net_velocity = (zone.inflow_rate - zone.outflow_rate) * 5
                zone.last_updated = datetime.utcnow().isoformat() + "Z"

            # 3. Auto-populate TODO lists
            self._populate_todo_lists()

            # 4. Flow-Rate and Predictive Anomaly Detection
            self._detect_flow_rate_anomalies()

    def _populate_todo_lists(self):
        from src.domain.deterministic_rules import get_predetermined_suggestions
        for _zid, zone in self._zones.items():
            ratio = zone.current_occupancy / zone.max_capacity if zone.max_capacity > 0 else 0
            pct = ratio * 100
            zone.todo_list = get_predetermined_suggestions(zone.node_type, pct)

    def _detect_flow_rate_anomalies(self):
        for zone_id, zone in self._zones.items():
            if zone.throughput_capacity_pph <= 0:
                continue
            
            # 1. CASCADE_RISK: predictive analytics based on net_velocity
            current_occ = zone.current_occupancy
            threshold = zone.max_capacity * 0.90
            
            if current_occ < threshold and zone.net_velocity > 0:
                time_to_breach_min = (threshold - current_occ) / zone.net_velocity
                if time_to_breach_min <= 10:
                    already_queued = any(
                        a.get("zone_id") == zone_id and a.get("type") == "CASCADE_RISK"
                        for a in self._anomaly_queue
                    )
                    if not already_queued:
                        self._anomaly_queue.append({
                            "type": "CASCADE_RISK", "zone_id": zone_id,
                            "time_to_breach_min": round(time_to_breach_min, 1),
                            "net_velocity": zone.net_velocity,
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        })
                        self._alerts.append(
                            f"[PREDICTIVE ALERT] '{zone_id}' will breach 90% capacity in {round(time_to_breach_min, 1)} minutes at current net flow (+{zone.net_velocity}/min)."
                        )
            
            # 2. FLOW_MISMATCH: throughput capacity vs actual flow
            actual_hourly_rate = (zone.inflow_rate + zone.outflow_rate) * 60
            flow_ratio = actual_hourly_rate / zone.throughput_capacity_pph
            
            if flow_ratio >= self.FLOW_RATE_ANOMALY_THRESHOLD:
                continue
            
            adjacent_congested = any(
                self._zones[adj_id].current_occupancy / self._zones[adj_id].max_capacity >= 0.70
                for adj_id in zone.connected_nodes if adj_id in self._zones
            )
            
            if not adjacent_congested:
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
                f"[FLOW ANOMALY] '{zone_id}' bottleneck detected. Adjacent zones congested but throughput is only {actual_hourly_rate} pph vs {zone.throughput_capacity_pph} pph capacity."
            )
