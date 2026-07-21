import asyncio
import json
import logging
import os
import traceback
from datetime import UTC, datetime

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.domain.state import StadiumStateManager
from src.routers.api import api_router

# Configure global backend logging (stdout only)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ArenaPulse-AI Volunteer Co-Pilot",
    description="Agentic crowd operations & translation control deck for stadium volunteers.",
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}")
    logger.error(traceback.format_exc())

    # Write to canonical JSON log per error-observability.md
    log_path = os.path.join("data", "error_logs.json")
    os.makedirs("data", exist_ok=True)

    try:
        if os.path.exists(log_path):
            with open(log_path, encoding="utf-8") as f:
                logs = json.load(f)
        else:
            logs = []
    except Exception:
        logs = []

    error_entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "error_type": type(exc).__name__,
        "component": f"{request.method} {request.url.path}",
        "message": str(exc),
        "stack_trace_summary": traceback.format_exc()[:500],
        "status": "UNRESOLVED",
        "resolution_strategy": None,
    }
    logs.append(error_entry)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

    return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "message": str(exc)})


app.include_router(api_router)
app.mount("/static", StaticFiles(directory="static"), name="static")
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
