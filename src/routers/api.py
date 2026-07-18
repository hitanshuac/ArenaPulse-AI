import asyncio
import csv
import io
import json
import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.domain.agent import VolunteerAgent
from src.domain.state import StadiumStateManager, ZoneModel

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
    """Server-Sent Events endpoint pushing real-time stadium telemetry, system metrics, and closed-loop alerts."""
    async def event_generator():
        while True:
            state = await state_manager.get_all_zones()
            alerts = await state_manager.flush_alerts()
            payload = {
                "zones": state,
                "system": {
                    "quota_used": stadium_agent.llm_client.daily_calls_made,
                    "quota_limit": stadium_agent.llm_client.DAILY_LIMIT,
                    "cache_size": len(stadium_agent.llm_client.response_cache),
                    "llm_trust_failures": stadium_agent.validation_failure_count,
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

@api_router.post("/agent/run")
async def run_agent_workflow(force_llm: bool = Form(False)):
    """
    Triggers the agent to evaluate the active telemetry state and fire workflows.

    Closed-Loop Validation Pipeline:
        L1 (Schema Gate) — handled inside VolunteerAgent.process_telemetry()
        L2 (Topology Gate) — validated here before applying mitigations to state
        State Snapshot — taken before any LLM-driven mutation for rollback safety
    """
    state = await state_manager.get_all_zones()
    if not state:
        raise HTTPException(status_code=400, detail="Operational state database is empty.")

    result = stadium_agent.process_telemetry(state, force_llm=force_llm)

    # L2 Topology Gate: validate and apply physical mitigations to state manager
    tasks = result.get("tasks", [])
    if tasks:
        # Snapshot state before LLM-driven mutations
        await state_manager.snapshot_state()
        bottlenecks = await state_manager.identify_bottleneck_zones()

        applied_count = 0
        rejected_count = 0
        topology_alerts: list[str] = []

        for task in tasks:
            args = task.get("arguments", {})
            zone_id = args.get("zone_id")
            instructions = args.get("instructions")

            if not zone_id or not instructions:
                topology_alerts.append(
                    f"[L2 TOPOLOGY REJECTION] Task missing zone_id or instructions: {args}"
                )
                rejected_count += 1
                continue

            # L2: Verify the proposed zone is upstream of at least one bottleneck
            is_valid_upstream = False
            if bottlenecks:
                for bottleneck_id in bottlenecks:
                    if await state_manager.validate_upstream_mitigation(bottleneck_id, zone_id):
                        is_valid_upstream = True
                        break

            if not is_valid_upstream and bottlenecks:
                topology_alerts.append(
                    f"[L2 TOPOLOGY REJECTION] '{zone_id}' is not upstream of any bottleneck "
                    f"{bottlenecks}. Mitigation '{instructions}' blocked."
                )
                rejected_count += 1
                continue

            # Passed L2 — apply mitigation
            applied = await state_manager.update_mitigation(zone_id, instructions)
            if applied:
                applied_count += 1
            else:
                rejected_count += 1

        # If ALL tasks were rejected by L2, rollback state
        if applied_count == 0 and rejected_count > 0:
            await state_manager.rollback_state()
            topology_alerts.append(
                "[L2 FULL REJECTION] All LLM-proposed mitigations failed topology validation. "
                "State rolled back to pre-LLM snapshot."
            )

        # Merge topology alerts into result
        existing_alerts = result.get("alerts", [])
        existing_alerts.extend(topology_alerts)
        if existing_alerts:
            result["alerts"] = existing_alerts

        # Add application summary to execution trace
        trace = result.get("execution_trace", [])
        trace.append(
            f"[L2 GATE SUMMARY] Applied: {applied_count}, Rejected: {rejected_count}"
        )
        result["execution_trace"] = trace

    return result

@api_router.post("/translate")
async def translate_query(query: str = Form(...), force_llm: bool = Form(False)):
    """Processes verbal input to assess priority and translates the instructions."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query text must be valid.")
    return stadium_agent.interpret_fan_query(query, force_llm=force_llm)
