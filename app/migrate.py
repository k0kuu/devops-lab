import os
import time
import psycopg

for attempt in range(30):
    try:
        with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=3) as conn:
            # Serialize concurrent initializers, including two API replicas.
            conn.execute("SELECT pg_advisory_xact_lock(424242)")
            conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version integer PRIMARY KEY)")
            applied = conn.execute("SELECT 1 FROM schema_migrations WHERE version=1").fetchone()
            if not applied:
                conn.execute("CREATE TABLE items (id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY, name text NOT NULL)")
                conn.execute("INSERT INTO schema_migrations(version) VALUES (1)")
        print("Migration 1 applied or already present", flush=True)
        break
    except psycopg.OperationalError:
        if attempt == 29:
            raise
        time.sleep(2)
