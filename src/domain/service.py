import logging
from typing import Any

from src.domain.agent import VolunteerAgent
from src.domain.narrative_client import NarrativeLLMClient
from src.domain.state import StadiumStateManager

logger = logging.getLogger(__name__)


class StadiumApplicationService:
    """
    Application Service orchestrating business logic between the
    State Manager and the LLM Agents.
    Keeps the presentation (routers) layer clean.
    """

    def __init__(self):
        self.state_manager = StadiumStateManager()
        self.stadium_agent = VolunteerAgent()
        self.narrative_client = NarrativeLLMClient()

    async def run_agent_workflow(self) -> dict[str, Any]:
        """Runs deterministic anomaly detection and builds execution trace."""
        state = await self.state_manager.get_all_zones()
        if not state:
            raise ValueError("Operational state database is empty.")

        result = self.stadium_agent.process_telemetry(state)

        anomaly_queue = await self.state_manager.get_anomaly_queue()
        result["anomaly_count"] = len(anomaly_queue)
        if anomaly_queue:
            result["execution_trace"].append(
                f"[Anomaly Queue] {len(anomaly_queue)} pending anomalies detected by flow-rate analysis."
            )
            for anomaly in anomaly_queue:
                a_type = anomaly.get("type", "UNKNOWN")
                a_zone = anomaly.get("zone_id", "?")
                if a_type == "FLOW_MISMATCH":
                    result["execution_trace"].append(
                        f"  → [{a_type}] '{a_zone}': actual flow {anomaly.get('actual_flow_pph', '?')} pph "
                        f"vs capacity {anomaly.get('capacity_pph', '?')} pph"
                    )
                else:
                    result["execution_trace"].append(f"  → [{a_type}] '{a_zone}': {anomaly.get('action', 'pending')}")

        return result

    async def analyze_anomalies(self) -> dict[str, Any]:
        """Fires the LLM for spatial anomaly analysis and updates state mitigations."""
        anomaly_queue = await self.state_manager.get_anomaly_queue()

        if not anomaly_queue:
            return {
                "decision": "[NO ANOMALIES] Queue is empty. No spatial analysis needed.",
                "execution_trace": ["[Queue Empty] Run diagnostics first to detect anomalies."],
            }

        state = await self.state_manager.get_all_zones()

        # Fire the LLM
        result = self.stadium_agent.analyze_spatial_anomaly(anomaly_queue, state)

        # Apply validated redistributions to state if analysis succeeded
        analyses = result.get("analyses", [])
        if analyses:
            await self.state_manager.snapshot_state()
            applied_count = 0

            for analysis in analyses:
                for redist in analysis.get("redistributions", []):
                    zone_id = redist.get("zone_id")
                    reduce_pct = redist.get("reduce_flow_pct", 0)
                    reasoning = redist.get("reasoning", "")

                    mitigation_label = f"Flow reduced {reduce_pct}%: {reasoning[:60]}"
                    applied = await self.state_manager.update_mitigation(zone_id, mitigation_label)
                    if applied:
                        applied_count += 1

            trace = result.get("execution_trace", [])
            trace.append(f"[L2 GATE SUMMARY] Applied: {applied_count} flow redistributions")
            result["execution_trace"] = trace

            # Flush the anomaly queue on successful analysis
            await self.state_manager.flush_anomaly_queue()

        return result

    async def translate_query(self, query: str) -> dict[str, Any]:
        """Translates queries and conditionally triggers routing anomalies."""
        if not query.strip():
            raise ValueError("Query text must be valid.")

        result = self.stadium_agent.interpret_fan_query(query)

        # If CRITICAL, auto-queue a medical routing anomaly for LLM analysis
        if result.get("requires_llm_routing"):
            await self.state_manager.append_anomaly(
                {
                    "type": "MEDICAL_ROUTING",
                    "zone_id": "FIELD_REPORT",
                    "query": query,
                    "translated_en": result.get("translated_response_en", ""),
                    "action": "MEDICAL EMERGENCY — Requires multi-node crowd routing decision",
                    "timestamp": result.get("translated_response_en", ""),
                }
            )

        return result
