"""Check the telemetry rows written by scripts/e2e_telemetry.sh.

Reads the database directly (``DATABASE_URL``), so it checks what was stored,
not what the API answered. Skipped unless the script sets
``TELEMETRY_E2E_EXPECTED_ROWS``.
"""

import os

import pytest
from sqlalchemy import create_engine, inspect, text

# The fields docs/how-to/telemetry.md lists, plus the row id.
ALLOWED_COLUMNS = {
    "id",
    "timestamp",
    "telemetry_level",
    "os",
    "country_name",
    "country_iso_code",
    "region",
    "cloud_provider",
    "cloud_region",
    "cpu_count",
    "cpu_physical_count",
    "cpu_model",
    "cpu_architecture",
    "gpu_count",
    "gpu_model",
    "gpu_memory_total_gb",
    "gpu_driver_version",
    "cuda_version",
    "cudnn_version",
    "ram_total_size_gb",
    "python_version",
    "python_implementation",
    "python_env_type",
    "codecarbon_version",
    "codecarbon_install_method",
}

pytestmark = [
    pytest.mark.integ_test,
    pytest.mark.skipif(
        not os.getenv("TELEMETRY_E2E_EXPECTED_ROWS"),
        reason="run through scripts/e2e_telemetry.sh",
    ),
]


@pytest.fixture(scope="module")
def engine():
    return create_engine(os.environ["DATABASE_URL"])


def test_table_has_no_coordinates_and_only_allowed_columns(engine):
    columns = {column["name"] for column in inspect(engine).get_columns("telemetry")}
    assert not {"latitude", "longitude"} & columns
    assert columns <= ALLOWED_COLUMNS


def test_one_minimal_row_per_process(engine):
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM telemetry")).mappings().all()

    for row in rows:
        print({key: value for key, value in row.items() if key != "id"})
    assert len(rows) == int(os.environ["TELEMETRY_E2E_EXPECTED_ROWS"])
    for row in rows:
        assert row["telemetry_level"] == "minimal"
        assert {key for key, value in row.items() if value is not None} <= (
            ALLOWED_COLUMNS
        )
