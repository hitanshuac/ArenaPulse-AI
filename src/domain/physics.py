from datetime import UTC, datetime
from typing import Any

from src.domain.models import ZoneModel


def build_gravity_map(zones: dict[str, ZoneModel]) -> dict[str, float]:
    """Precomputes distances to 'sinks' for fluid dynamic routing."""
    # Gravity levels: Seating=0, Corridors=1, Turnstiles=2, Plazas=3.5, External=4
    gmap = {}
    for zid, z in zones.items():
        if z.node_type == "seating":
            gmap[zid] = 0
        elif z.node_type == "amenity":
            gmap[zid] = 1
        elif z.node_type == "corridor":
            gmap[zid] = 2
        elif z.node_type == "turnstile":
            gmap[zid] = 3
        elif z.node_type == "external":
            if "Plaza" in zid:
                gmap[zid] = 3.5
            else:
                gmap[zid] = 4
    return gmap


def populate_todo_lists(zones: dict[str, ZoneModel]):
    from src.domain.deterministic_rules import get_predetermined_suggestions

    for _zid, zone in zones.items():
        ratio = zone.current_occupancy / zone.max_capacity if zone.max_capacity > 0 else 0
        pct = ratio * 100
        zone.todo_list = get_predetermined_suggestions(
            zone.node_type,
            pct,
            length_m=zone.length_m,
            width_m=zone.width_m,
            connected_nodes=zone.connected_nodes,
        )


def prune_stale_anomalies(
    zones: dict[str, ZoneModel], anomaly_queue: list[dict[str, Any]]
):
    """Remove anomalies whose conditions no longer hold. Prevents infinite queue growth."""
    still_valid = []
    for anomaly in anomaly_queue:
        zone_id = anomaly.get("zone_id", "")
        a_type = anomaly.get("type", "")

        if zone_id not in zones:
            continue  # Zone removed — drop anomaly

        zone = zones[zone_id]
        occupancy_pct = (zone.current_occupancy / zone.max_capacity * 100) if zone.max_capacity > 0 else 0

        if a_type == "CASCADE_RISK":
            # Keep only if zone is still gaining and above 75%
            if zone.net_velocity > 0 and occupancy_pct >= 75:
                still_valid.append(anomaly)
        elif a_type == "FLOW_MISMATCH":
            # Keep only if adjacent zones are still heavily congested (>80%)
            adjacent_heavily_congested = any(
                (zones[adj_id].current_occupancy / zones[adj_id].max_capacity) >= 0.80
                for adj_id in zone.connected_nodes
                if adj_id in zones and zones[adj_id].max_capacity > 0
            )
            if adjacent_heavily_congested:
                still_valid.append(anomaly)
        elif a_type == "MEDICAL_ROUTING":
            still_valid.append(anomaly)  # Medical anomalies persist until manually resolved
        else:
            still_valid.append(anomaly)

    anomaly_queue.clear()
    anomaly_queue.extend(still_valid)


def apply_deterministic_mitigations(
    zones: dict[str, ZoneModel], anomaly_queue: list[dict[str, Any]], alerts: list[str]
):
    """
    Auto-applies countermeasures for known anomaly patterns without needing the LLM.
    Orange protocol: restrict 1 upstream node. Red protocol: lock down ALL connected nodes.
    Staffing numbers are derived from physical zone dimensions.
    """
    from src.domain.deterministic_rules import calculate_staffing

    resolved_indices = []

    for idx, anomaly in enumerate(anomaly_queue):
        zone_id = anomaly.get("zone_id", "")
        a_type = anomaly.get("type", "")

        if zone_id not in zones:
            resolved_indices.append(idx)
            continue

        zone = zones[zone_id]
        occupancy_pct = (zone.current_occupancy / zone.max_capacity * 100) if zone.max_capacity > 0 else 0
        staff = calculate_staffing(zone.length_m, zone.width_m)

        if a_type == "CASCADE_RISK" and occupancy_pct >= 90:
            # RED PROTOCOL: Lock down ALL connected nodes
            if not zone.mitigation_active:
                zone.mitigation_active = (
                    f"Auto: HOLD all inflow. Deploy {staff['coordinators']} coordinators, "
                    f"{staff['barriers']} barriers"
                )
                for adj_id in zone.connected_nodes:
                    if adj_id in zones and not zones[adj_id].mitigation_active:
                        zones[adj_id].mitigation_active = f"Auto: HOLD — '{zone_id}' at {occupancy_pct:.0f}%"
                connected_list = ", ".join(zone.connected_nodes)
                alerts.append(
                    f"[AUTO-MITIGATION] 🔴 RED '{zone_id}' at {occupancy_pct:.0f}%. "
                    f"Perimeter lockdown on [{connected_list}]. "
                    f"Deploy {staff['coordinators']} coordinators across {zone.length_m:.0f}m."
                )
                resolved_indices.append(idx)

        elif a_type == "CASCADE_RISK" and occupancy_pct >= 70:
            # ORANGE PROTOCOL: Throttle first upstream node only
            if not zone.mitigation_active:
                upstream = zone.connected_nodes[0] if zone.connected_nodes else None
                if upstream and upstream in zones and not zones[upstream].mitigation_active:
                    zones[upstream].mitigation_active = f"Auto: Throttled 30% — '{zone_id}' rising"
                zone.mitigation_active = (
                    f"Auto: Upstream '{upstream}' throttled 30%. "
                    f"Deploy {staff['coordinators']} coordinators"
                )
                alerts.append(
                    f"[AUTO-MITIGATION] 🟠 ORANGE '{zone_id}' at {occupancy_pct:.0f}%. "
                    f"Upstream '{upstream}' throttled 30%. "
                    f"Deploy {staff['coordinators']} coordinators across {zone.length_m:.0f}m."
                )
                resolved_indices.append(idx)

        elif a_type == "FLOW_MISMATCH":
            # Apply flow rebalance with staffing
            if not zone.mitigation_active:
                zone.mitigation_active = (
                    f"Auto: Flow rebalance. {staff['coordinators']} coordinators deployed"
                )
                alerts.append(
                    f"[AUTO-MITIGATION] '{zone_id}' flow rebalance activated. "
                    f"Deploy {staff['coordinators']} coordinators at 25m intervals across {zone.length_m:.0f}m."
                )
                resolved_indices.append(idx)

    # Remove resolved anomalies (iterate in reverse to preserve indices)
    for idx in sorted(resolved_indices, reverse=True):
        if idx < len(anomaly_queue):
            anomaly_queue.pop(idx)


def clear_expired_mitigations(zones: dict[str, ZoneModel]):
    """Auto-clear mitigations on zones that have dropped back below 70%."""
    for zone in zones.values():
        if not zone.mitigation_active:
            continue
        if not zone.mitigation_active.startswith("Auto:"):
            continue  # Only auto-clear deterministic mitigations, not LLM ones
        occupancy_pct = (zone.current_occupancy / zone.max_capacity * 100) if zone.max_capacity > 0 else 0
        if occupancy_pct < 65:
            zone.mitigation_active = None


def detect_flow_rate_anomalies(
    zones: dict[str, ZoneModel], anomaly_queue: list[dict[str, Any]], alerts: list[str], threshold: float = 0.10
):
    # Step 0: Prune stale anomalies and clear expired mitigations first
    prune_stale_anomalies(zones, anomaly_queue)
    clear_expired_mitigations(zones)

    for zone_id, zone in zones.items():
        if zone.throughput_capacity_pph <= 0:
            continue

        # 1. CASCADE_RISK: predictive analytics based on net_velocity
        current_occ = zone.current_occupancy
        capacity_threshold = zone.max_capacity * 0.90

        if current_occ < capacity_threshold and zone.net_velocity > 0:
            time_to_breach_min = (capacity_threshold - current_occ) / zone.net_velocity
            if time_to_breach_min <= 10:
                already_queued = any(
                    a.get("zone_id") == zone_id and a.get("type") == "CASCADE_RISK" for a in anomaly_queue
                )
                if not already_queued:
                    anomaly_queue.append(
                        {
                            "type": "CASCADE_RISK",
                            "zone_id": zone_id,
                            "time_to_breach_min": round(time_to_breach_min, 1),
                            "net_velocity": zone.net_velocity,
                            "timestamp": datetime.now(UTC).isoformat() + "Z",
                        }
                    )
                    alerts.append(
                        f"[PREDICTIVE ALERT] '{zone_id}' will breach 90% capacity in {round(time_to_breach_min, 1)} minutes at current net flow (+{zone.net_velocity}/min)."
                    )

        # 2. FLOW_MISMATCH: throughput capacity vs actual flow
        # Only flag if actual flow is below threshold AND adjacent zones are heavily congested (>80%)
        actual_hourly_rate = (zone.inflow_rate + zone.outflow_rate) * 60
        flow_ratio = actual_hourly_rate / zone.throughput_capacity_pph

        if flow_ratio >= threshold:
            continue

        # Require HEAVY adjacent congestion (80%+), not just moderate (70%)
        adjacent_heavily_congested = any(
            zones[adj_id].current_occupancy / zones[adj_id].max_capacity >= 0.80
            for adj_id in zone.connected_nodes
            if adj_id in zones and zones[adj_id].max_capacity > 0
        )

        if not adjacent_heavily_congested:
            continue

        already_queued = any(a.get("zone_id") == zone_id and a.get("type") == "FLOW_MISMATCH" for a in anomaly_queue)
        if already_queued:
            continue
        anomaly_queue.append(
            {
                "type": "FLOW_MISMATCH",
                "zone_id": zone_id,
                "actual_flow_pph": actual_hourly_rate,
                "capacity_pph": zone.throughput_capacity_pph,
                "flow_ratio": round(flow_ratio, 2),
                "width_m": zone.width_m,
                "length_m": zone.length_m,
                "timestamp": datetime.now(UTC).isoformat() + "Z",
            }
        )
        alerts.append(
            f"[FLOW ANOMALY] '{zone_id}' bottleneck detected. Adjacent zones congested but throughput is only {actual_hourly_rate} pph vs {zone.throughput_capacity_pph} pph capacity."
        )

    # Step 3: Apply deterministic auto-mitigations for any new anomalies
    apply_deterministic_mitigations(zones, anomaly_queue, alerts)


def simulate_physics_tick(
    zones: dict[str, ZoneModel],
    current_phase: str,
    gravity_map: dict[str, float],
    anomaly_queue: list[dict[str, Any]],
    alerts: list[str],
    anomaly_threshold: float = 0.25,
):
    """
    Pure physics engine tick. Mutates the zones, anomaly_queue, and alerts in-place.
    Zero-Sum implementation: strictly conserves crowd numbers.
    """
    # Reset tick velocities
    for z in zones.values():
        z.inflow_rate = int(z.inflow_rate * 0.5)
        z.outflow_rate = int(z.outflow_rate * 0.5)

    # Track projected occupancy to prevent the overfill race condition
    projected_occ = {zid: z.current_occupancy for zid, z in zones.items()}

    # 2. Simulate Fluid Dynamics (Phase-Gravity)
    transfers = []  # (from_id, to_id, amount)

    for zone_id, zone in zones.items():
        if not zone.connected_nodes or zone.current_occupancy <= 0:
            continue

        # Determine valid downstream neighbors based on phase and gravity
        valid_neighbors = []
        for neighbor_id in zone.connected_nodes:
            if neighbor_id not in zones:
                continue

            my_g = gravity_map.get(zone_id, 2)
            nbr_g = gravity_map.get(neighbor_id, 2)
            neighbor_zone = zones[neighbor_id]

            is_valid = False
            if neighbor_zone.node_type == "amenity":
                if (projected_occ[neighbor_id] / neighbor_zone.max_capacity) < 0.7:
                    is_valid = True
            elif zone.node_type == "amenity":
                is_valid = True  # Amenities can drain to any connected node
            else:
                if current_phase == "INGRESS" and my_g > nbr_g:
                    is_valid = True
                elif current_phase == "EGRESS" and my_g < nbr_g:
                    is_valid = True
                elif current_phase == "MATCH" and my_g > nbr_g:
                    is_valid = True

            if is_valid:
                valid_neighbors.append(neighbor_id)

        if not valid_neighbors:
            continue

        # Distribute intended flow proportionally across valid neighbors
        for neighbor_id in valid_neighbors:
            neighbor_zone = zones[neighbor_id]

            flow_amount = 0

            if neighbor_zone.node_type == "amenity":
                flow_amount = int((zone.current_occupancy * 0.01) / len(valid_neighbors))
            elif zone.node_type == "amenity":
                flow_amount = int((zone.current_occupancy * 0.15) / len(valid_neighbors))
            else:
                if current_phase == "INGRESS":
                    flow_amount = int((zone.current_occupancy * 0.1) / len(valid_neighbors))
                elif current_phase == "EGRESS":
                    flow_amount = int((zone.current_occupancy * 0.15) / len(valid_neighbors))
                elif current_phase == "MATCH":
                    flow_amount = int((zone.current_occupancy * 0.02) / len(valid_neighbors))

            if flow_amount > 0:
                if zone.mitigation_active:
                    flow_amount = int(flow_amount * 0.2)

                max_flow_per_minute = int(min(zone.throughput_capacity_pph, neighbor_zone.throughput_capacity_pph) / 60)
                # Divvy up the throughput capacity for this node across neighbors
                flow_amount = min(flow_amount, int(max_flow_per_minute / len(valid_neighbors)))

                available_space = neighbor_zone.max_capacity - projected_occ[neighbor_id]
                flow_amount = min(flow_amount, available_space)

                # Make sure we don't transfer more than we have left
                flow_amount = min(flow_amount, projected_occ[zone_id])

                if flow_amount > 0:
                    transfers.append((zone_id, neighbor_id, flow_amount))
                    # Immediately update projected occupancy to prevent race condition
                    projected_occ[neighbor_id] += flow_amount
                    projected_occ[zone_id] -= flow_amount

    # Apply transfers
    for source, sink, amount in transfers:
        if zones[source].current_occupancy >= amount:
            zones[source].current_occupancy -= amount
            zones[source].outflow_rate += amount

            zones[sink].current_occupancy += amount
            zones[sink].inflow_rate += amount

    # Update net velocities
    for zone in zones.values():
        zone.net_velocity = zone.inflow_rate - zone.outflow_rate
        zone.last_updated = datetime.now(UTC).isoformat() + "Z"

    # 3. Auto-populate TODO lists
    populate_todo_lists(zones)

    # 4. Flow-Rate and Predictive Anomaly Detection
    detect_flow_rate_anomalies(zones, anomaly_queue, alerts, anomaly_threshold)
