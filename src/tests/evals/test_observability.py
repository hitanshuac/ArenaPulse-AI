import json

from src.capabilities.observability import log_error


def test_error_logging(tmp_path):
    log_file = tmp_path / "test_errors.json"

    try:
        _ = 1 / 0
    except ZeroDivisionError as e:
        log_error(e, "test_component", str(log_file))

    assert log_file.exists()
    with open(log_file) as f:
        data = [json.loads(line) for line in f]

    assert len(data) == 1
    assert data[0]["error_type"] == "ZeroDivisionError"
    assert data[0]["status"] == "UNRESOLVED"
