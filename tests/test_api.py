import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

def test_get_stadium_state():
    """Unit: Verifies the default active stadium state returns cleanly."""
    response = client.get("/api/stadium")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "zone_id" in data[0]
        assert "current_occupancy" in data[0]

def test_update_telemetry():
    """Unit: Verifies a single zone's occupancy can be mutated via POST."""
    response = client.post(
        "/api/update-telemetry",
        data={"zone_id": "Zone A (North Gate)", "current_occupancy": 4500}
    )
    assert response.status_code == 200
    assert "recorded" in response.json()["message"]

    # Verify change
    state_res = client.get("/api/stadium")
    for zone in state_res.json():
        if zone["zone_id"] == "Zone A (North Gate)":
            assert zone["current_occupancy"] == 4500

def test_update_telemetry_not_found():
    """Unit: Ensures gracefully failing on non-existent zones."""
    response = client.post(
        "/api/update-telemetry",
        data={"zone_id": "Ghost Zone", "current_occupancy": 100}
    )
    assert response.status_code == 404

def test_upload_csv_success():
    """Integration/IO: Validates replacing the entire operational state via CSV upload."""
    file_path = os.path.join(FIXTURES_DIR, "stadium_canonical.csv")
    with open(file_path, "rb") as f:
        response = client.post(
            "/api/upload-csv",
            files={"file": ("stadium_canonical.csv", f, "text/csv")}
        )
    assert response.status_code == 200
    assert response.json()["records"] == 3

def test_upload_csv_invalid_schema():
    """Integration/IO: Ensures malformed CSV headers trigger an HTTP 400 safely."""
    file_path = os.path.join(FIXTURES_DIR, "stadium_invalid.csv")
    with open(file_path, "rb") as f:
        response = client.post(
            "/api/upload-csv",
            files={"file": ("stadium_invalid.csv", f, "text/csv")}
        )
    assert response.status_code == 400
    assert "Malformed template" in response.json()["detail"]
