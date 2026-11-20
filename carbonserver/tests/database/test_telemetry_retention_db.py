"""Real-Postgres check for the telemetry retention trigger (see
``20260927_add_telemetry_table.py``): rows older than 3 years must be purged
on the next insert, and recent rows must survive.

Requires a live Postgres reachable via ``DATABASE_URL`` with the telemetry
migration already applied. Skipped unless ``DATABASE_URL`` is set.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, text

pytestmark = [
    pytest.mark.integ_test,
    pytest.mark.skipif(
        not os.getenv("DATABASE_URL"), reason="requires a live Postgres DATABASE_URL"
    ),
]


@pytest.fixture(scope="module")
def engine():
    return create_engine(os.environ["DATABASE_URL"])


def _insert(conn, timestamp):
    row_id = uuid.uuid4()
    conn.execute(
        text(
            "INSERT INTO telemetry (id, timestamp, telemetry_level) "
            "VALUES (:id, :ts, 'minimal')"
        ),
        {"id": row_id, "ts": timestamp},
    )
    conn.commit()
    return row_id


def test_old_rows_are_purged_on_next_insert_and_recent_rows_survive(engine):
    now = datetime.now(timezone.utc)
    with engine.connect() as conn:
        old_row_id = _insert(conn, now - timedelta(days=4 * 365))
        recent_row_id = _insert(conn, now)
        # A further insert fires the AFTER INSERT statement trigger that
        # purges anything older than 3 years.
        trigger_row_id = _insert(conn, now)

        ids = {
            row[0] for row in conn.execute(text("SELECT id FROM telemetry")).fetchall()
        }
    assert old_row_id not in ids
    assert recent_row_id in ids
    assert trigger_row_id in ids
