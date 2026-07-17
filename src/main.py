import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from src.routers.api import api_router
from src.domain.state import StadiumStateManager

app = FastAPI(
    title="ArenaPulse-AI Volunteer Co-Pilot",
    description="Agentic crowd operations & translation control deck for stadium volunteers."
)

app.include_router(api_router)
state_manager = StadiumStateManager()

@app.on_event("startup")
async def start_iot_simulation():
    """Background Python task generating dynamic telemetry curves and calculating velocity."""
    async def simulation_loop():
        while True:
            await asyncio.sleep(4)
            await state_manager.simulate_iot_tick()
    asyncio.create_task(simulation_loop())

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    static_path = os.path.join("static", "index.html")
    if not os.path.exists(static_path):
        raise HTTPException(status_code=404, detail="Dashboard index.html template file not found.")
    with open(static_path, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
