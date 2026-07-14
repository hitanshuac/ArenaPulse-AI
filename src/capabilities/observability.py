import json
import os
import traceback
from datetime import datetime


def log_error(error, component, error_logs_path="data/error_logs.json"):
    os.makedirs(os.path.dirname(error_logs_path), exist_ok=True)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "error_type": type(error).__name__,
        "component": component,
        "stack_trace_summary": traceback.format_exc()[-500:],  # keep it compressed
        "status": "UNRESOLVED",
    }

    with open(error_logs_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return log_entry
