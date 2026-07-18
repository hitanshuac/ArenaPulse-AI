import logging
from typing import Any

from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

# CRITICAL keywords that trigger immediate local alarm
CRITICAL_KEYWORDS = frozenset({
    "medico", "dolor", "herido", "hospital", "emergencia", "auxilio", "sangre",
    "pain", "hurt", "medical", "doctor", "emergency", "help", "blood",
    "ambulance", "ambulancia", "lost child", "niño perdido", "fire", "fuego",
    "unconscious", "inconsciente", "breathing", "respirar"
})

# ---------------------------------------------------------------------------
# Predetermined Suggestions by Node Type and Threshold
# ---------------------------------------------------------------------------

SUGGESTIONS_MAP: dict[str, dict[str, list[str]]] = {
    "external": {
        "green": [],
        "orange": ["Activate overflow parking signage", "Deploy traffic marshals to direct vehicles"],
        "red": ["Close incoming vehicle lanes", "Redirect to satellite parking", "Request shuttle bus deployment"],
        "critical": ["EMERGENCY: Evacuate parking structure", "Activate emergency vehicle lanes"]
    },
    "turnstile": {
        "green": [],
        "orange": ["Open additional scanning lanes", "Deploy manual ticket verification staff"],
        "red": ["Activate overflow bypass lanes", "Deploy crowd control barriers", "Halt inbound flow temporarily"],
        "critical": ["EMERGENCY: Open emergency bypass gates", "Deploy security to manage crowd crush risk"]
    },
    "corridor": {
        "green": [],
        "orange": ["Activate one-way flow protocol", "Deploy flow barriers at junctions"],
        "red": ["Restrict upstream gate throughput", "Deploy barriers to split crowd stream", "Open emergency side corridors"],
        "critical": ["EMERGENCY: Clear corridor immediately", "Activate PA system for rerouting"]
    },
    "amenity": {
        "green": [],
        "orange": ["Deploy additional service staff", "Open overflow facility if available"],
        "red": ["Redirect visitors to alternate facility", "Deploy portable units", "Implement queue management system"],
        "critical": ["EMERGENCY: Evacuate facility", "Deploy medical team if Medical Bay"]
    },
    "seating": {
        "green": [],
        "orange": ["Monitor section entry points", "Pre-stage ushers at section boundaries"],
        "red": ["Halt section entry temporarily", "Redirect to adjacent section", "Deploy crowd density monitors"],
        "critical": ["EMERGENCY: Begin section evacuation protocol", "Activate emergency lighting and PA"]
    }
}


def get_predetermined_suggestions(node_type: str, occupancy_pct: float) -> list[str]:
    """Returns predetermined action items based on node type and occupancy percentage."""
    type_map = SUGGESTIONS_MAP.get(node_type, SUGGESTIONS_MAP["corridor"])

    if occupancy_pct >= 90.0:
        return type_map["red"]
    elif occupancy_pct >= 70.0:
        return type_map["orange"]
    else:
        return type_map["green"]


def run_deterministic_crowd_analysis(zones: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Evaluates zones deterministically without calling external APIs.
    Returns structured anomaly actions with upstream zone IDs from DAG topology.
    """
    critical_zones = []
    anomalies = []

    for zone in zones:
        try:
            capacity = float(zone.get("max_capacity", 1))
            occupancy = float(zone.get("current_occupancy", 0))
            ratio = occupancy / capacity if capacity > 0 else 0
            percentage = round(ratio * 100, 1)

            if percentage >= 70.0:
                zone_data = {
                    "zone_id": zone.get("zone_id", "Unknown"),
                    "percentage": percentage,
                    "gates": zone.get("associated_gates", "N/A"),
                    "node_type": zone.get("node_type", "corridor"),
                    "upstream_nodes": zone.get("upstream_nodes", [])
                }
                critical_zones.append(zone_data)

                if percentage >= 80.0:
                    upstream = zone.get("upstream_nodes", [])
                    divert_to = upstream[0] if upstream else "N/A"
                    anomalies.append({
                        "type": "THRESHOLD_BREACH",
                        "zone_id": zone_data["zone_id"],
                        "percentage": percentage,
                        "divert_to": divert_to,
                        "action": f"DIVERT traffic from {divert_to} away from {zone_data['zone_id']}"
                    })
        except Exception:
            continue

    execution_trace = []
    if critical_zones:
        for cz in critical_zones:
            severity = "🔴 RED" if cz["percentage"] >= 90 else "🟠 ORANGE"
            execution_trace.append(
                f"[{severity}] {cz['zone_id']} at {cz['percentage']}% ({cz['node_type']})"
            )
            if cz["upstream_nodes"]:
                execution_trace.append(
                    f"  → [Math Router] Throttle upstream: {', '.join(cz['upstream_nodes'])}"
                )
        decision = f"Rule engine detected {len(critical_zones)} zones above 70% threshold."
    else:
        decision = "All zones operating within safe parameters (<70%)."
        execution_trace.append("[All Clear] Telemetry values are green across all 15 nodes.")

    return {
        "decision": decision,
        "execution_trace": execution_trace,
        "anomalies": anomalies
    }


def detect_critical_intent(query: str) -> bool:
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in CRITICAL_KEYWORDS)


def translate_fan_query(query: str, target_lang: str = "en") -> str:
    try:
        translated = GoogleTranslator(source="auto", target=target_lang).translate(query)
        return translated if translated else query
    except Exception as exc:
        logger.warning("Google Translate failed: %s. Returning original.", exc)
        return query


def run_deterministic_translation(user_query: str) -> dict[str, Any]:
    is_critical = detect_critical_intent(user_query)
    translated_en = translate_fan_query(user_query, target_lang="en")
    translated_es = translate_fan_query(user_query, target_lang="es")

    if is_critical:
        return {
            "urgency_level": "CRITICAL",
            "detected_intent": "Medical/Safety Emergency Priority",
            "translated_response_en": f"EMERGENCY DETECTED: {translated_en}. Medical team alerted.",
            "translated_response_es": f"EMERGENCIA DETECTADA: {translated_es}. Equipo médico alertado.",
            "requires_llm_routing": True
        }

    return {
        "urgency_level": "CASUAL",
        "detected_intent": "General Navigation Request",
        "translated_response_en": translated_en,
        "translated_response_es": translated_es,
        "requires_llm_routing": False
    }
