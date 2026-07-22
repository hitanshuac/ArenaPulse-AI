import asyncio
import csv
import io
import json
import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.domain.models import ZoneModel
from src.domain.service import StadiumApplicationService
from src.domain.state import StadiumStateManager

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api")
state_manager = StadiumStateManager()
app_service = StadiumApplicationService()


@api_router.get("/stadium", response_model=list[ZoneModel])
async def get_stadium_state():
    """Returns the current snapshot of the stadium's zone states."""
    state = await state_manager.get_all_zones()
    return state


@api_router.get("/stadium/stream")
async def stadium_stream():
    """Server-Sent Events endpoint pushing real-time stadium telemetry, system metrics, anomaly queue, and alerts."""

    async def event_generator():
        while True:
            state = await state_manager.get_all_zones()
            alerts = await state_manager.flush_alerts()
            anomaly_queue = await state_manager.get_anomaly_queue()
            payload = {
                "zones": state,
                "system": {
                    "quota_used": app_service.stadium_agent.llm_client.daily_calls_made,
                    "quota_limit": app_service.stadium_agent.llm_client.DAILY_LIMIT,
                    "cache_size": len(app_service.stadium_agent.llm_client.response_cache),
                    "llm_trust_failures": app_service.stadium_agent.validation_failure_count,
                    "anomaly_count": len(anomaly_queue),
                    "alerts": alerts,
                    "current_phase": state_manager.current_phase,
                    "match_minute": state_manager.match_minute,
                    "match_running": state_manager.match_running,
                },
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@api_router.get("/stadium/narrative-stream")
async def get_stadium_narrative():
    """Server-Sent Events endpoint pushing unconstrained LLM narrative text."""
    state = await state_manager.get_all_zones()

    # Compress state to a readable summary to save tokens
    summary = []
    for z in state:
        pct = (z.get("current_occupancy", 0) / z.get("max_capacity", 1)) * 100
        if pct > 60:
            summary.append(f"{z.get('zone_id')} ({pct:.0f}%)")

    state_str = "Critical zones: " + (", ".join(summary) if summary else "None. All clear.")

    return StreamingResponse(app_service.narrative_client.generate_narrative_stream(state_str), media_type="text/event-stream")


@api_router.post("/update-telemetry")
async def update_telemetry(zone_id: str = Form(...), current_occupancy: int = Form(...)):
    """Allows simulating incoming live telemetry data packets."""
    updated = await state_manager.update_zone_occupancy(zone_id, current_occupancy)
    if not updated:
        raise HTTPException(status_code=404, detail="Stadium zone not found.")
    state = await state_manager.get_all_zones()
    return {"message": "Telemetry metrics recorded", "zones": state}


@api_router.post("/upload-csv")
async def upload_stadium_data(file: UploadFile = File(...)):
    """Accepts CSV updates for evaluations. Allows testing dynamic capabilities."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Unsupported file format. Must be a .csv file.")

    contents = await file.read()
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    temp_state = []
    try:
        for row in reader:
            temp_state.append(
                {
                    "zone_id": row["zone_id"].strip(),
                    "node_type": "corridor",  # default fallback
                    "current_occupancy": int(row["current_occupancy"].strip()),
                    "max_capacity": int(row["max_capacity"].strip()),
                    "associated_gates": row["associated_gates"].strip(),
                    "velocity": 0,
                }
            )
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Malformed template. Columns required: zone_id, current_occupancy, max_capacity, associated_gates.",
        )

    await state_manager.apply_bulk_update(temp_state)
    state = await state_manager.get_all_zones()
    return {"message": "Live operational telemetry successfully overwritten.", "records": len(state)}


@api_router.post("/stadium/reset")
async def reset_stadium_topology():
    """Resets the topology to the default 15-node FIFA layout."""
    state_manager._init_state()
    return {"message": "Topology reset to 15 nodes."}


@api_router.post("/stadium/phase")
async def change_stadium_phase(phase: str = Form(...)):
    """Changes the macroscopic flow phase (INGRESS, MATCH, EGRESS)."""
    await state_manager.set_phase(phase.upper())
    return {"message": f"Phase updated to {phase.upper()}"}


@api_router.post("/agent/run")
async def run_agent_workflow():
    """
    Purely deterministic telemetry analysis. Costs 0 API tokens.

    Runs the Math Router to identify threshold breaches and returns
    the current anomaly queue. The "Run Diagnostics" button calls this freely.
    """
    try:
        return await app_service.run_agent_workflow()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/agent/analyze")
async def analyze_anomalies():
    """
    The ONLY endpoint that fires the LLM. Costs 1 API call.

    HITL Gate: Only fires when the Commander explicitly clicks "Analyze Anomalies".
    Batches all queued anomalies into a single prompt and asks the LLM to determine
    multi-node flow redistribution percentages based on physical corridor dimensions.

    The LLM does NOT identify problems (deterministic engine already did).
    The LLM determines which nodes should have flow REDUCED and by how much.
    """
    return await app_service.analyze_anomalies()


@api_router.post("/translate")
async def translate_query(query: str = Form(...)):
    """
    Processes fan input using Google Translate (free, 0 API tokens).
    CRITICAL keyword screening is done locally via regex.

    If a CRITICAL emergency is detected, the response includes
    requires_llm_routing=True to signal the frontend that the Commander
    should trigger spatial analysis for crowd routing.
    """
    try:
        return await app_service.translate_query(query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
