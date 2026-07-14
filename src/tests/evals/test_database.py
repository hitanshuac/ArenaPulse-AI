from src.capabilities.database import ingest_data_idempotent, init_duckdb


def test_duckdb_idempotency():
    conn = init_duckdb()
    records = [(i, f"data_{i}") for i in range(1000)]

    # Ingest 3 times
    ingest_data_idempotent(conn, records)
    ingest_data_idempotent(conn, records)
    ingest_data_idempotent(conn, records)

    # Count rows, should be exactly 1000
    res = conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()
    assert res[0] == 1000

    # Check memory limit pragma
    mem_limit = conn.execute("SELECT current_setting('memory_limit')").fetchone()
    assert mem_limit is not None
