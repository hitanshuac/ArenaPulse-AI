import csv
import io
import json
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
import asyncio

from src.domain.state import StadiumStateManager, ZoneModel
from src.domain.agent import VolunteerAgent

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
    """Server-Sent Events endpoint pushing real-time stadium telemetry."""
    async def event_generator():
        while True:
            state = await state_manager.get_all_zones()
            yield f"data: {json.dumps(state)}\n\n"
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
    """Triggers the agent to evaluate the active telemetry state and fire workflows."""
    state = await state_manager.get_all_zones()
    if not state:
        raise HTTPException(status_code=400, detail="Operational state database is empty.")
    return stadium_agent.process_telemetry(state, force_llm=force_llm)

@api_router.post("/translate")
async def translate_query(query: str = Form(...), force_llm: bool = Form(False)):
    """Processes verbal input to assess priority and translates the instructions."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query text must be valid.")
    return stadium_agent.interpret_fan_query(query, force_llm=force_llm)
