import pytest
from fastapi.testclient import TestClient
import os

from src.main import app

client = TestClient(app)

def test_upload_stadium_data():
    fixture_path = os.path.join("tests", "fixtures", "stadium_canonical.csv")
    if not os.path.exists(fixture_path):
        pytest.skip("Fixture not found")

    with open(fixture_path, "rb") as f:
        response = client.post("/api/upload-csv", files={"file": ("stadium_canonical.csv", f, "text/csv")})
    
    assert response.status_code == 200
    assert "Live operational telemetry successfully overwritten." in response.json()["message"]
    assert "records" in response.json()
