from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

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

    last_updated: str = Field(default_factory=lambda: datetime.now(UTC).isoformat() + "Z", description="ISO timestamp")

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


class FlowRedistributionModel(BaseModel):
    """Schema for a single node's flow adjustment in the LLM's redistribution plan."""

    zone_id: str = Field(..., min_length=1, description="Target zone to adjust")
    reduce_flow_pct: int = Field(..., ge=0, le=100, description="Percentage to reduce flow at this node (0-100)")
    reasoning: str = Field(
        ..., min_length=1, description="Why this node needs adjustment based on physical constraints"
    )


class SpatialAnalysisModel(BaseModel):
    """Strict schema for the LLM's multi-node spatial physics analysis."""

    risk_type: Literal["FLOW_MISMATCH", "MEDICAL_ROUTING", "CASCADE_RISK"] = Field(
        ..., description="Classification of the spatial anomaly"
    )
    analysis: str = Field(
        ...,
        min_length=1,
        description="LLM's spatial reasoning explanation considering corridor dimensions and flow rates",
    )
    redistributions: list[FlowRedistributionModel] = Field(
        ..., min_length=1, description="Ordered list of nodes to adjust flow at"
    )
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(..., description="Overall urgency")


class SpatialAnalysisEnvelopeModel(BaseModel):
    """Wrapper for the full LLM response containing one or more analyses."""

    analyses: list[SpatialAnalysisModel] = Field(
        ..., min_length=1, description="List of spatial analyses for each anomaly"
    )


class ValidationResult:
    """Encapsulates the outcome of L1 schema validation with alert metadata."""

    def __init__(self, valid: bool, data: Any = None, alerts: list[str] | None = None):
        self.valid = valid
        self.data = data
        self.alerts = alerts or []
