import json
import os

from pydantic import BaseModel, ValidationError


class TelemetryRecord(BaseModel):
    id: int
    payload: str
    tier: str


def validate_and_route(records_data, quarantine_dir="data"):
    valid_records = []
    quarantined = []

    for data in records_data:
        try:
            record = TelemetryRecord(**data)
            valid_records.append(record.model_dump())
        except ValidationError as e:
            quarantined.append({"raw_data": data, "error": str(e)})

    if quarantined:
        os.makedirs(quarantine_dir, exist_ok=True)
        # Using JSON instead of parquet for simplicity in mock,
        # but concept holds true: we isolate the malformed data.
        with open(os.path.join(quarantine_dir, "quarantine_dlq.json"), "a") as f:
            for q in quarantined:
                f.write(json.dumps(q) + "\n")

    return valid_records, quarantined
