import asyncio
import json
import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.domain.agent import VolunteerAgent
from src.domain.deterministic_rules import detect_critical_intent
from src.domain.state import StadiumStateManager, ZoneModel

import csv
import io

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api")
state_manager = StadiumStateManager()
stadium_agent = VolunteerAgent()


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
                    "quota_used": stadium_agent.llm_client.daily_calls_made,
                    "quota_limit": stadium_agent.llm_client.DAILY_LIMIT,
                    "cache_size": len(stadium_agent.llm_client.response_cache),
                    "llm_trust_failures": stadium_agent.validation_failure_count,
                    "anomaly_count": len(anomaly_queue),
                    "alerts": alerts
                }
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(2)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Unsupported file format. Must be a .csv file.")

    contents = await file.read()
    decoded = contents.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))

    temp_state = []
    try:
        for row in reader:
            temp_state.append({
                "zone_id": row["zone_id"].strip(),
                "node_type": "corridor", # default fallback
                "current_occupancy": int(row["current_occupancy"].strip()),
                "max_capacity": int(row["max_capacity"].strip()),
                "associated_gates": row["associated_gates"].strip(),
                "velocity": 0
            })
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Malformed template. Columns required: zone_id, current_occupancy, max_capacity, associated_gates."
        )

    await state_manager.apply_bulk_update(temp_state)
    state = await state_manager.get_all_zones()
    return {"message": "Live operational telemetry successfully overwritten.", "records": len(state)}

@api_router.post("/stadium/reset")
async def reset_stadium_topology():
    """Resets the topology to the default 15-node FIFA layout."""
    state_manager._init_state()
    return {"message": "Topology reset to 15 nodes."}

@api_router.post("/agent/run")
async def run_agent_workflow():
    """
    Purely deterministic telemetry analysis. Costs 0 API tokens.

    Runs the Math Router to identify threshold breaches and returns
    the current anomaly queue. The "Run Diagnostics" button calls this freely.
    """
    state = await state_manager.get_all_zones()
    if not state:
        raise HTTPException(status_code=400, detail="Operational state database is empty.")

    result = stadium_agent.process_telemetry(state)

    # Include the current anomaly queue in the response
    anomaly_queue = await state_manager.get_anomaly_queue()
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
                result["execution_trace"].append(
                    f"  → [{a_type}] '{a_zone}': {anomaly.get('action', 'pending')}"
                )

    return result


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
    anomaly_queue = await state_manager.get_anomaly_queue()

    if not anomaly_queue:
        return {
            "decision": "[NO ANOMALIES] Queue is empty. No spatial analysis needed.",
            "execution_trace": ["[Queue Empty] Run diagnostics first to detect anomalies."]
        }

    state = await state_manager.get_all_zones()

    # Fire the LLM — single API call for all queued anomalies
    result = stadium_agent.analyze_spatial_anomaly(anomaly_queue, state)

    # Apply validated redistributions to state if analysis succeeded
    analyses = result.get("analyses", [])
    if analyses:
        await state_manager.snapshot_state()
        applied_count = 0

        for analysis in analyses:
            for redist in analysis.get("redistributions", []):
                zone_id = redist.get("zone_id")
                reduce_pct = redist.get("reduce_flow_pct", 0)
                reasoning = redist.get("reasoning", "")

                mitigation_label = f"Flow reduced {reduce_pct}%: {reasoning[:60]}"
                applied = await state_manager.update_mitigation(zone_id, mitigation_label)
                if applied:
                    applied_count += 1

        trace = result.get("execution_trace", [])
        trace.append(f"[L2 GATE SUMMARY] Applied: {applied_count} flow redistributions")
        result["execution_trace"] = trace

        # Flush the anomaly queue on successful analysis
        await state_manager.flush_anomaly_queue()

    return result


@api_router.post("/translate")
async def translate_query(query: str = Form(...)):
    """
    Processes fan input using Google Translate (free, 0 API tokens).
    CRITICAL keyword screening is done locally via regex.

    If a CRITICAL emergency is detected, the response includes
    requires_llm_routing=True to signal the frontend that the Commander
    should trigger spatial analysis for crowd routing.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query text must be valid.")

    result = stadium_agent.interpret_fan_query(query)

    # If CRITICAL, auto-queue a medical routing anomaly for LLM analysis
    if result.get("requires_llm_routing"):
        await state_manager.append_anomaly({
            "type": "MEDICAL_ROUTING",
            "zone_id": "FIELD_REPORT",
            "query": query,
            "translated_en": result.get("translated_response_en", ""),
            "action": "MEDICAL EMERGENCY — Requires multi-node crowd routing decision",
            "timestamp": result.get("translated_response_en", "")
        })

    return result
