import duckdb


def init_duckdb(db_path=":memory:"):
    conn = duckdb.connect(db_path)
    # Configure WAL and Memory Limits per duckdb-optimizer skill
    if db_path != ":memory:":
        conn.execute("PRAGMA wal_autocheckpoint='1GB'")
    conn.execute("PRAGMA memory_limit='256MB'")

    # Create the target table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY,
            payload VARCHAR,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return conn


def ingest_data_idempotent(conn, records):
    """
    Ingests records into DuckDB idempotently.
    Uses INSERT OR REPLACE to prevent duplicate rows on retry.
    Records should be a list of tuples: (id, payload)
    """
    conn.execute("BEGIN TRANSACTION")
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO telemetry (id, payload)
            VALUES (?, ?)
        """,
            records,
        )
        conn.execute("COMMIT")
    except Exception as e:
        conn.execute("ROLLBACK")
        raise e
