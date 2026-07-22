from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class RuleResult(BaseModel):
    allowed: bool = Field(..., description="Whether the proposed stadium crowd action is permitted")
    rule_name: str = Field(..., description="Name of the evaluated rule")
    reason: str = Field(..., description="Detailed justification for allowance or denial")
    sanitized_payload: Any = Field(default=None, description="Sanitized action payload if modified")


class BaseRule(ABC):
    name: str = "BaseRule"

    @abstractmethod
    def evaluate(self, action_type: str, payload: Any) -> RuleResult:
        """Evaluates a stadium operational payload against deterministic rules."""
        pass


class StadiumCapacityRule(BaseRule):
    """Rule preventing dangerous overcrowding breaches (>95% capacity)."""

    name = "StadiumCapacityRule"

    def __init__(self, critical_threshold_pct: float = 95.0):
        self.critical_threshold_pct = critical_threshold_pct

    def evaluate(self, action_type: str, payload: Any) -> RuleResult:
        if action_type not in ("update_occupancy", "zone_check"):
            return RuleResult(allowed=True, rule_name=self.name, reason="Action type not governed by capacity rule.")

        if isinstance(payload, dict):
            occupancy = payload.get("current_occupancy", payload.get("occupancy", 0))
            max_cap = payload.get("max_capacity", 1)
            zone_id = payload.get("zone_id", "Unknown")
        else:
            occupancy = getattr(payload, "current_occupancy", getattr(payload, "occupancy", 0))
            max_cap = getattr(payload, "max_capacity", 1)
            zone_id = getattr(payload, "zone_id", "Unknown")

        pct = (occupancy / max_cap * 100) if max_cap > 0 else 0
        if pct >= self.critical_threshold_pct:
            return RuleResult(
                allowed=False,
                rule_name=self.name,
                reason=f"CRITICAL OVERCROWDING: Zone '{zone_id}' at {pct:.1f}% capacity ({occupancy}/{max_cap}). Gate closure mandated."
            )

        return RuleResult(
            allowed=True,
            rule_name=self.name,
            reason=f"Zone '{zone_id}' occupancy within safe threshold ({pct:.1f}%).",
            sanitized_payload=payload
        )


class CrowdFlowRateRule(BaseRule):
    """Rule preventing corridor inflow rates from exceeding physical throughput capacity."""

    name = "CrowdFlowRateRule"

    def evaluate(self, action_type: str, payload: Any) -> RuleResult:
        if action_type != "adjust_flow":
            return RuleResult(allowed=True, rule_name=self.name, reason="Action type not governed by flow rate rule.")

        inflow = payload.get("inflow_rate", 0) if isinstance(payload, dict) else getattr(payload, "inflow_rate", 0)
        max_throughput = (payload.get("throughput_capacity_pph", 3000) if isinstance(payload, dict) else getattr(payload, "throughput_capacity_pph", 3000)) / 60.0  # Convert to fans/min

        if inflow > max_throughput:
            return RuleResult(
                allowed=False,
                rule_name=self.name,
                reason=f"STAMPEDE RISK: Inflow rate of {inflow} fans/min exceeds corridor throughput limit ({max_throughput:.0f} fans/min)."
            )

        return RuleResult(
            allowed=True,
            rule_name=self.name,
            reason="Inflow rate within physical corridor throughput capacity.",
            sanitized_payload=payload
        )


class StadiumStateTransitionRule(BaseRule):
    """Rule enforcing match timeline progression (INGRESS -> MATCH -> EGRESS)."""

    name = "StadiumStateTransitionRule"

    def __init__(self):
        self.allowed_phases = {
            "INGRESS": ["MATCH"],
            "MATCH": ["EGRESS"],
            "EGRESS": ["CLEANUP"],
            "CLEANUP": ["INGRESS"]
        }

    def evaluate(self, action_type: str, payload: Any) -> RuleResult:
        if action_type != "set_match_phase":
            return RuleResult(allowed=True, rule_name=self.name, reason="Action type not governed by match phase rule.")

        current_phase = payload.get("current_phase") if isinstance(payload, dict) else getattr(payload, "current_phase", None)
        target_phase = payload.get("target_phase") if isinstance(payload, dict) else getattr(payload, "target_phase", None)

        if not current_phase or not target_phase:
            return RuleResult(allowed=False, rule_name=self.name, reason="Missing match phase transition metadata.")

        valid_next = self.allowed_phases.get(current_phase, [])
        if target_phase not in valid_next:
            return RuleResult(
                allowed=False,
                rule_name=self.name,
                reason=f"Illegal match phase jump from '{current_phase}' to '{target_phase}'. Allowed: {valid_next}"
            )

        return RuleResult(
            allowed=True,
            rule_name=self.name,
            reason=f"Match phase shift from '{current_phase}' to '{target_phase}' approved.",
            sanitized_payload=payload
        )
