from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_update_telemetry_endpoint():
    """Validates the API routes and backend state mutations work synchronously."""
    # Send an update
    response = client.post("/api/update-telemetry", data={"zone_id": "Gate A", "current_occupancy": 7777})

    assert response.status_code == 200
    assert response.json()["message"] == "Telemetry metrics recorded"

    # Verify the state actually updated via the GET route
    state_res = client.get("/api/stadium")
    assert state_res.status_code == 200

    zones = state_res.json()
    zone_a = next(z for z in zones if z["zone_id"] == "Gate A")

    assert zone_a["current_occupancy"] == 7777
