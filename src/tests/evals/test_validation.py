import json

from src.capabilities.validation import validate_and_route


def test_pydantic_dlq(tmp_path):
    records = [
        {"id": 1, "payload": "A", "tier": "gold"},
        {"id": "bad", "payload": "B", "tier": "silver"},  # Malformed ID
        {"id": 3, "payload": "C", "tier": "bronze"},
    ]

    valid, quarantined = validate_and_route(records, quarantine_dir=str(tmp_path))

    assert len(valid) == 2
    assert len(quarantined) == 1

    # Check if file was written
    dlq_file = tmp_path / "quarantine_dlq.json"
    assert dlq_file.exists()

    with open(dlq_file) as f:
        data = [json.loads(line) for line in f]

    assert len(data) == 1
    assert data[0]["raw_data"]["id"] == "bad"
