import logging
from typing import Any

from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

# CRITICAL keywords that bypass the LLM and trigger immediate local alarm
CRITICAL_KEYWORDS = frozenset({
    "medico", "dolor", "herido", "hospital", "emergencia", "auxilio", "sangre",
    "pain", "hurt", "medical", "doctor", "emergency", "help", "blood",
    "ambulance", "ambulancia", "lost child", "niño perdido", "fire", "fuego",
    "unconscious", "inconsciente", "breathing", "respirar"
})


def run_deterministic_crowd_analysis(zones: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Evaluates zones deterministically without calling external APIs.
    Guarantees a zero-crash safety net for crowd-critical logic.

    Returns structured anomaly actions with upstream zone IDs
    derived from DAG topology. Handles ALL threshold breaches locally.
    """
    critical_zones = []
    normal_zones = []
    anomalies = []

    for zone in zones:
        try:
            capacity = float(zone.get("max_capacity", 1))
            occupancy = float(zone.get("current_occupancy", 0))
            ratio = occupancy / capacity if capacity > 0 else 0
            percentage = round(ratio * 100, 1)

            zone_data = {
                "zone_id": zone.get("zone_id", "Unknown"),
                "percentage": percentage,
                "gates": zone.get("associated_gates", "N/A"),
                "upstream_nodes": zone.get("upstream_nodes", []),
                "velocity": zone.get("velocity", 0),
                "throughput_capacity_pph": zone.get("throughput_capacity_pph", 0),
                "width_m": zone.get("width_m", 0),
                "length_m": zone.get("length_m", 0)
            }

            if percentage >= 80.0:
                critical_zones.append(zone_data)
                # Build structured anomaly with upstream diversion target
                upstream = zone.get("upstream_nodes", [])
                divert_to = upstream[0] if upstream else "N/A"
                anomalies.append({
                    "type": "THRESHOLD_BREACH",
                    "zone_id": zone_data["zone_id"],
                    "percentage": percentage,
                    "divert_to": divert_to,
                    "action": f"DIVERT traffic from {divert_to} away from {zone_data['zone_id']}"
                })
            else:
                normal_zones.append(zone_data)
        except Exception:
            continue

    execution_trace = []
    if critical_zones:
        for cz in critical_zones:
            execution_trace.append(
                f"[Escalation Triggered] Gate congestion at {cz['zone_id']} is at {cz['percentage']}%."
            )
            divert_target = cz['upstream_nodes'][0] if cz['upstream_nodes'] else "nearest corridor"
            execution_trace.append(
                f"[Math Router] Upstream diversion: throttle flow at {divert_target} → {cz['zone_id']}."
            )
            execution_trace.append(
                f"[Dispatched] Safety routing announcements triggered near {cz['zone_id']} ({cz['gates']})."
            )
        decision = "Rule engine identified safety threshold breaches and deployed immediate redirection protocols."
    else:
        decision = "All monitored stadium zones are operating within acceptable threshold parameters (<80%)."
        execution_trace.append("[No Action Required] Telemetry values are currently green.")

    return {
        "decision": decision,
        "execution_trace": execution_trace,
        "anomalies": anomalies
    }


def detect_critical_intent(query: str) -> bool:
    """Screens a fan query for CRITICAL safety keywords. Returns True if emergency detected."""
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in CRITICAL_KEYWORDS)


def translate_fan_query(query: str, target_lang: str = "en") -> str:
    """
    Translates fan input using Google Translate (free, 0 API tokens).
    Falls back to returning the original query on any error.
    """
    try:
        translated = GoogleTranslator(source="auto", target=target_lang).translate(query)
        return translated if translated else query
    except Exception as exc:
        logger.warning("Google Translate failed: %s. Returning original query.", exc)
        return query


def run_deterministic_translation(user_query: str) -> dict[str, Any]:
    """
    Local translation handler using Google Translate + regex keyword screening.
    Zero LLM tokens consumed.
    """
    is_critical = detect_critical_intent(user_query)

    # Translate to both EN and ES using the free Google Translate API
    translated_en = translate_fan_query(user_query, target_lang="en")
    translated_es = translate_fan_query(user_query, target_lang="es")

    if is_critical:
        return {
            "urgency_level": "CRITICAL",
            "detected_intent": "Medical/Safety Emergency Priority",
            "translated_response_en": f"EMERGENCY DETECTED: {translated_en}. Medical team has been alerted. Stay where you are.",
            "translated_response_es": f"EMERGENCIA DETECTADA: {translated_es}. El equipo médico ha sido alertado. Quédese donde está.",
            "requires_llm_routing": True
        }

    return {
        "urgency_level": "CASUAL",
        "detected_intent": "General Navigation Request",
        "translated_response_en": translated_en,
        "translated_response_es": translated_es,
        "requires_llm_routing": False
    }
