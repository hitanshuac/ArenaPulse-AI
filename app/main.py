import asyncio
import csv
import io
import json
import os
import random

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.agent_engine import VolunteerAgent

app = FastAPI(
    title="ArenaPulse-AI Volunteer Co-Pilot",
    description="Agentic crowd operations & translation control deck for stadium volunteers."
)

stadium_agent = VolunteerAgent()

# Internal simulated in-memory state
active_stadium_state = [
    {"zone_id": "Zone A (North Gate)", "current_occupancy": 3200, "max_capacity": 8000, "associated_gates": "Gates 1-2", "velocity": 0},
    {"zone_id": "Zone B (East Gate)", "current_occupancy": 5100, "max_capacity": 8000, "associated_gates": "Gates 3-4", "velocity": 0},
    {"zone_id": "Zone C (South Gate)", "current_occupancy": 1500, "max_capacity": 8000, "associated_gates": "Gates 5-6", "velocity": 0},
]

class ZoneModel(BaseModel):
    zone_id: str = Field(..., description="Unique ID of the stadium zone")
    current_occupancy: int = Field(..., ge=0, description="Current occupancy metric")
    max_capacity: int = Field(..., gt=0, description="Max safe capacity threshold")
    associated_gates: str = Field(..., description="Physical gates serving the zone")
    velocity: int = Field(0, description="Rate of change (fans/min)")

@app.get("/api/stadium", response_model=list[ZoneModel])
def get_stadium_state():
    """Returns the current snapshot of the stadium's zone states."""
    return active_stadium_state

@app.on_event("startup")
async def start_iot_simulation():
    """Background Python task generating dynamic telemetry curves and calculating velocity."""
    async def simulation_loop():
        global active_stadium_state
        while True:
            await asyncio.sleep(4)
            for zone in active_stadium_state:
                # Stochastic addition
                addition = random.randint(10, 40)
                new_occ = min(zone["max_capacity"], zone["current_occupancy"] + addition)
                # Calculate velocity per minute (since tick is 4s, multiply by 15)
                actual_addition = new_occ - zone.get("current_occupancy", 0)
                zone["current_occupancy"] = new_occ
                zone["velocity"] = actual_addition * 15
    asyncio.create_task(simulation_loop())

@app.get("/api/stadium/stream")
async def stadium_stream():
    """Server-Sent Events endpoint pushing real-time stadium telemetry."""
    async def event_generator():
        while True:
            yield f"data: {json.dumps(active_stadium_state)}\n\n"
            await asyncio.sleep(2)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/update-telemetry")
def update_telemetry(zone_id: str = Form(...), current_occupancy: int = Form(...)):
    """Allows simulating incoming live telemetry data packets."""
    global active_stadium_state
    updated = False
    for zone in active_stadium_state:
        if zone["zone_id"] == zone_id:
            zone["current_occupancy"] = max(0, current_occupancy)
            updated = True
            break
    if not updated:
        raise HTTPException(status_code=404, detail="Stadium zone not found.")
    return {"message": "Telemetry metrics recorded", "zones": active_stadium_state}

@app.post("/api/upload-csv")
async def upload_stadium_data(file: UploadFile = File(...)):
    """
    Accepts CSV updates for evaluations.
    Allows testing dynamic capabilities.
    """
    global active_stadium_state
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

    active_stadium_state = temp_state
    return {"message": "Live operational telemetry successfully overwritten.", "records": len(active_stadium_state)}

@app.post("/api/agent/run")
def run_agent_workflow():
    """Triggers the agent to evaluate the active telemetry state and fire workflows."""
    if not active_stadium_state:
        raise HTTPException(status_code=400, detail="Operational state database is empty.")
    return stadium_agent.process_telemetry(active_stadium_state)

@app.post("/api/translate")
def translate_query(query: str = Form(...)):
    """Processes verbal input to assess priority and translates the instructions."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query text must be valid.")
    return stadium_agent.interpret_fan_query(query)

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    static_path = os.path.join("static", "index.html")
    if not os.path.exists(static_path):
        raise HTTPException(status_code=404, detail="Dashboard index.html template file not found.")
    with open(static_path, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
