import datetime
import json
import os
import subprocess

ERROR_LOG_PATH = "data/error_logs.json"


def get_latest_failed_run():
    """Fetches the ID of the latest failed GitHub Actions run."""
    try:
        result = subprocess.run(
            ["gh", "run", "list", "--status", "failure", "--limit", "1", "--json", "databaseId"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        if data and len(data) > 0:
            return data[0]["databaseId"]
        return None
    except subprocess.CalledProcessError as e:
        print(f"Failed to fetch runs: {e.stderr}")
        return None


def fetch_run_logs(run_id):
    """Fetches the log for the failed steps of a specific run."""
    try:
        result = subprocess.run(
            ["gh", "run", "view", str(run_id), "--log-failed"], capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Failed to fetch logs for run {run_id}: {e.stderr}")
        return None


def summarize_log(raw_log):
    """Summarizes a raw CI/CD log to prevent context window bloat."""
    lines = raw_log.splitlines()
    # Take the last 50 lines to keep it highly compressed, as errors usually appear at the end
    compressed = "\n".join(lines[-50:])
    if len(lines) > 50:
        compressed = f"... ({len(lines) - 50} lines truncated) ...\n" + compressed
    return compressed


def inject_to_error_logs(run_id, compressed_log):
    """Injects the compressed log directly into data/error_logs.json."""
    os.makedirs(os.path.dirname(ERROR_LOG_PATH), exist_ok=True)

    error_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "error_type": "CI/CD Remote Failure",
        "component": f"GitHub Actions Run #{run_id}",
        "stack_trace_summary": compressed_log,
        "status": "UNRESOLVED",
        "resolution_strategy": "",
    }

    try:
        if os.path.exists(ERROR_LOG_PATH):
            with open(ERROR_LOG_PATH) as f:
                content = f.read().strip()
                if content.startswith("[") and content.endswith("]"):
                    logs = json.loads(content)
                else:
                    logs = []
                    for line in content.splitlines():
                        line = line.strip()
                        if line.startswith("{") and line.endswith("}"):
                            logs.append(json.loads(line))
        else:
            logs = []
    except Exception:
        logs = []

    logs.append(error_entry)

    with open(ERROR_LOG_PATH, "w") as f:
        json.dump(logs, f, indent=2)


def main():
    print("Checking for recent CI/CD pipeline failures...")
    run_id = get_latest_failed_run()

    if not run_id:
        print("No recent failed CI/CD runs found in this repository. All clear!")
        return

    print(f"Found failed run ID: {run_id}. Fetching remote logs...")
    raw_log = fetch_run_logs(run_id)

    if not raw_log:
        print("Could not retrieve log details.")
        return

    print("Compressing logs and injecting into local observability pipeline...")
    compressed = summarize_log(raw_log)
    inject_to_error_logs(run_id, compressed)

    print("SUCCESS: Remote CI/CD error successfully ported to data/error_logs.json!")
    print("The agent can now read the logs locally and fix the code.")


if __name__ == "__main__":
    main()
