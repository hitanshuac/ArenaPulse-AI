import json
import logging
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from src.domain.deterministic_rules import run_deterministic_crowd_analysis, run_deterministic_translation, detect_critical_intent
from src.security.secure_llm_client import SecureLLMClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# L1 Schema Gate: Pydantic validators for LLM spatial analysis output
# ---------------------------------------------------------------------------


class FlowRedistributionModel(BaseModel):
    """Schema for a single node's flow adjustment in the LLM's redistribution plan."""
    zone_id: str = Field(..., min_length=1, description="Target zone to adjust")
    reduce_flow_pct: int = Field(..., ge=0, le=100, description="Percentage to reduce flow at this node (0-100)")
    reasoning: str = Field(..., min_length=1, description="Why this node needs adjustment based on physical constraints")


class SpatialAnalysisModel(BaseModel):
    """Strict schema for the LLM's multi-node spatial physics analysis."""
    risk_type: Literal["FLOW_MISMATCH", "MEDICAL_ROUTING", "CASCADE_RISK"] = Field(
        ..., description="Classification of the spatial anomaly"
    )
    analysis: str = Field(..., min_length=1, description="LLM's spatial reasoning explanation considering corridor dimensions and flow rates")
    redistributions: list[FlowRedistributionModel] = Field(
        ..., min_length=1, description="Ordered list of nodes to adjust flow at"
    )
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(..., description="Overall urgency")


class SpatialAnalysisEnvelopeModel(BaseModel):
    """Wrapper for the full LLM response containing one or more analyses."""
    analyses: list[SpatialAnalysisModel] = Field(
        ..., min_length=1, description="List of spatial analyses for each anomaly"
    )


# ---------------------------------------------------------------------------
# Validation result container for closed-loop observability
# ---------------------------------------------------------------------------

class ValidationResult:
    """Encapsulates the outcome of L1 schema validation with alert metadata."""

    def __init__(self, valid: bool, data: Any = None, alerts: list[str] | None = None):
        self.valid = valid
        self.data = data
        self.alerts = alerts or []


def validate_spatial_analysis(raw_data: Any) -> ValidationResult:
    """L1 Schema Gate: Validates raw LLM output against SpatialAnalysisEnvelopeModel."""
    try:
        validated = SpatialAnalysisEnvelopeModel.model_validate(raw_data)
        return ValidationResult(valid=True, data=validated.model_dump())
    except ValidationError as exc:
        return ValidationResult(
            valid=False,
            alerts=[
                f"[L1 SCHEMA REJECTION] Spatial analysis rejected: {exc.error_count()} errors. "
                f"First error: {exc.errors()[0]['msg']}"
            ]
        )


class VolunteerAgent:
    def __init__(self):
        self.llm_client = SecureLLMClient()
        self.validation_failure_count = 0
        self.FAILURE_BUDGET = 3  # After N failures, auto-disable LLM

    def _is_trust_exhausted(self) -> bool:
        """SRE error budget: if too many LLM outputs fail validation, force edge mode."""
        return self.validation_failure_count >= self.FAILURE_BUDGET

    def process_telemetry(self, zones: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Purely deterministic telemetry processing. Costs 0 API tokens.
        Runs the Math Router to identify threshold breaches and returns
        structured anomaly actions.
        """
        result = run_deterministic_crowd_analysis(zones)
        result["decision"] = "[EDGE COMPUTE] " + result["decision"]
        return result

    def interpret_fan_query(self, query: str) -> dict[str, Any]:
        """
        Processes fan input using Google Translate (free) and local CRITICAL keyword detection.
        Costs 0 API tokens. Returns requires_llm_routing=True if a medical emergency
        needs LLM-driven multi-node crowd routing.
        """
        return run_deterministic_translation(query)

    def analyze_spatial_anomaly(self, anomalies: list[dict[str, Any]], zones: list[dict[str, Any]]) -> dict[str, Any]:
        """
        The ONLY method that calls the LLM. Costs 1 API call.

        Takes the deterministic anomaly queue + full zone state (including
        physical dimensions and flow rates) and asks the LLM to determine
        the optimal multi-node flow redistribution strategy.

        The LLM does NOT identify the problem (the deterministic engine already did).
        The LLM's job is to reason across multiple connected nodes simultaneously
        and determine which nodes should have flow REDUCED (not closed) and by
        what percentage, to optimally redistribute crowd pressure.
        """
        if not anomalies:
            return {
                "decision": "[NO ANOMALIES] Queue is empty. Nothing to analyze.",
                "execution_trace": []
            }

        # Error budget gate
        if self._is_trust_exhausted():
            return {
                "decision": f"[TRUST BUDGET EXHAUSTED - {self.validation_failure_count} failures] "
                            "LLM disabled. Clear anomalies manually.",
                "execution_trace": [],
                "alerts": [
                    f"[ERROR BUDGET] LLM disabled after {self.validation_failure_count} "
                    "consecutive validation failures."
                ]
            }

        # Build the spatial context for the LLM
        zone_topology = []
        for z in zones:
            zone_topology.append({
                "zone_id": z.get("zone_id"),
                "current_occupancy": z.get("current_occupancy"),
                "max_capacity": z.get("max_capacity"),
                "occupancy_pct": round(
                    (z.get("current_occupancy", 0) / z.get("max_capacity", 1)) * 100, 1
                ),
                "width_m": z.get("width_m"),
                "length_m": z.get("length_m"),
                "throughput_capacity_pph": z.get("throughput_capacity_pph"),
                "inflow_rate": z.get("inflow_rate"),
                "outflow_rate": z.get("outflow_rate"),
                "net_velocity": z.get("net_velocity"),
                "connected_nodes": z.get("connected_nodes", [])
            })

        prompt = f"""You are a spatial physics engine for a FIFA World Cup stadium.

STADIUM BIDIRECTIONAL TOPOLOGY (with physical corridor dimensions):
{json.dumps(zone_topology, indent=2)}

DETECTED ANOMALIES (identified by the deterministic engine — do NOT re-identify these):
{json.dumps(anomalies, indent=2)}

YOUR TASK: For each anomaly, determine the optimal multi-node flow REDISTRIBUTION strategy.
- You MUST NOT close any node entirely. Reduce flow percentage (0-100%) at specific nodes.
- Consider physical constraints: corridor width/length determines throughput capacity.
- Reason across ALL connected nodes simultaneously considering BIDIRECTIONAL net_velocity.
- If a node is congested but outflow_rate is high, the bottleneck is downstream.
- If a node is congested and inflow_rate is massive, the bottleneck is at the node itself or upstream.

Return strictly valid JSON matching this schema:
{{
  "analyses": [
    {{
      "risk_type": "FLOW_MISMATCH" | "MEDICAL_ROUTING" | "CASCADE_RISK",
      "analysis": "Your spatial reasoning considering corridor dimensions and flow rates",
      "redistributions": [
        {{
          "zone_id": "<NODE_ID>",
          "reduce_flow_pct": <0-100>,
          "reasoning": "Why this node needs adjustment"
        }}
      ],
      "priority": "HIGH" | "MEDIUM" | "LOW"
    }}
  ]
}}"""

        response = self.llm_client.generate_content(prompt, state_data=anomalies)

        if response["status"] == "quota_exhausted":
            return {
                "decision": "[QUOTA EXHAUSTED] Cannot analyze. Use deterministic fallback.",
                "execution_trace": [f"[Anomaly] {a.get('type', 'UNKNOWN')}: {a.get('zone_id', '?')}" for a in anomalies],
                "alerts": ["[QUOTA] Daily LLM limit reached. Anomalies remain in queue for manual review."]
            }

        if response["status"] == "error":
            return {
                "decision": f"[LLM ERROR] {response.get('error', 'Unknown error')}",
                "execution_trace": [],
                "alerts": [f"[LLM ERROR] {response.get('error', 'Unknown error')}"]
            }

        # L1 Schema Gate — validate BEFORE trusting
        raw_data = response["data"]
        validation = validate_spatial_analysis(raw_data)

        if not validation.valid:
            self.validation_failure_count += 1
            self.llm_client.invalidate_cache_for_state(anomalies)
            logger.warning("L1 Schema Gate rejected spatial analysis: %s", validation.alerts)

            return {
                "decision": "[L1 SCHEMA GATE - REJECTED] LLM output failed validation.",
                "execution_trace": [],
                "alerts": validation.alerts
            }

        # Schema passed — reset failure counter
        self.validation_failure_count = 0
        validated = validation.data

        prefix = (
            "[CACHED LLM]" if response["status"] == "cached"
            else f"[LIVE LLM - Call {self.llm_client.daily_calls_made}/{self.llm_client.DAILY_LIMIT}]"
        )

        execution_trace = []
        for analysis in validated.get("analyses", []):
            execution_trace.append(
                f"[{analysis['risk_type']}] {analysis['analysis']}"
            )
            for redist in analysis.get("redistributions", []):
                execution_trace.append(
                    f"  → Reduce flow at '{redist['zone_id']}' by {redist['reduce_flow_pct']}%: {redist['reasoning']}"
                )

        return {
            "decision": f"{prefix} Spatial analysis complete. {len(validated.get('analyses', []))} anomalies analyzed.",
            "execution_trace": execution_trace,
            "analyses": validated.get("analyses", []),
            "alerts": validation.alerts if validation.alerts else []
        }
