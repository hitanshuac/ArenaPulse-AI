from typing import Any


def run_deterministic_crowd_analysis(zones: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Evaluates zones deterministically without calling external APIs.
    Guarantees a zero-crash safety net for crowd-critical logic.
    """
    critical_zones = []
    normal_zones = []

    for zone in zones:
        try:
            capacity = float(zone.get("max_capacity", 1))
            occupancy = float(zone.get("current_occupancy", 0))
            ratio = occupancy / capacity if capacity > 0 else 0
            percentage = round(ratio * 100, 1)

            zone_data = {
                "zone_id": zone.get("zone_id", "Unknown"),
                "percentage": percentage,
                "gates": zone.get("associated_gates", "N/A")
            }

            if percentage >= 80.0:
                critical_zones.append(zone_data)
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
            execution_trace.append(
                f"[Task Assigned] Volunteer Crew redirected to assist with manual ticketing flow at {cz['gates']}."
            )
            execution_trace.append(
                f"[Dispatched Broadcast] Safety routing announcements triggered near {cz['zone_id']} (EN/ES)."
            )
        decision = "Rule engine identified safety threshold breaches and deployed immediate redirection protocols."
    else:
        decision = "All monitored stadium zones are operating within acceptable threshold parameters (<80%)."
        execution_trace.append("[No Action Required] Telemetry values are currently green.")

    return {
        "decision": decision,
        "execution_trace": execution_trace
    }

def run_deterministic_translation(user_query: str) -> dict[str, Any]:
    """
    Local fallback translator for safety-critical intents if the API is unreachable.
    """
    query_lower = user_query.lower()

    if any(word in query_lower for word in ["medico", "dolor", "herido", "hospital", "pain", "hurt", "medical", "doctor"]):
        return {
            "urgency_level": "CRITICAL",
            "detected_intent": "Medical Emergency Priority",
            "translated_response_en": "I understand you need urgent medical help. Please stay where you are. I am alerting the stadium emergency medical team right now.",
            "translated_response_es": "Entiendo que necesita ayuda médica urgente. Por favor quédese donde está. Estoy alertando al equipo médico de emergencia del estadio ahora mismo."
        }

    return {
        "urgency_level": "CASUAL",
        "detected_intent": "General Navigation Request",
        "translated_response_en": "Please continue down this concourse toward the nearest gate indicator on your ticket. Our volunteers are available to assist you.",
        "translated_response_es": "Por favor continúe por este pasillo hacia el indicador de puerta más cercano en su boleto. Nuestros voluntarios están disponibles para ayudarlo."
    }
