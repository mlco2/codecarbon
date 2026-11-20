"""add telemetry table

Revision ID: 20260927_add_telemetry
Revises: 20251119_add_utilization
Create Date: 2026-09-27 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260927_add_telemetry"
down_revision = "20251119_add_utilization"
branch_labels = None
depends_on = None

# New columns, as created by ``create_table`` for a fresh database. A naive
# timestamp is ambiguous across servers in different zones, so it is always
# timezone-aware (``timestamptz`` on Postgres).
NEW_COLUMNS = [
    sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    sa.Column("telemetry_level", sa.String, nullable=False),
    sa.Column("os", sa.String, nullable=True),
    sa.Column("country_name", sa.String, nullable=True),
    sa.Column("country_iso_code", sa.String, nullable=True),
    sa.Column("region", sa.String, nullable=True),
    sa.Column("cloud_provider", sa.String, nullable=True),
    sa.Column("cloud_region", sa.String, nullable=True),
    sa.Column("cpu_count", sa.Integer, nullable=True),
    sa.Column("cpu_physical_count", sa.Integer, nullable=True),
    sa.Column("cpu_model", sa.String, nullable=True),
    sa.Column("cpu_architecture", sa.String, nullable=True),
    sa.Column("gpu_count", sa.Integer, nullable=True),
    sa.Column("gpu_model", sa.String, nullable=True),
    sa.Column("gpu_driver_version", sa.String, nullable=True),
    sa.Column("gpu_memory_total_gb", sa.Float, nullable=True),
    sa.Column("ram_total_size_gb", sa.Float, nullable=True),
    sa.Column("cuda_version", sa.String, nullable=True),
    sa.Column("cudnn_version", sa.String, nullable=True),
    sa.Column("python_version", sa.String, nullable=True),
    sa.Column("python_implementation", sa.String, nullable=True),
    sa.Column("python_env_type", sa.String, nullable=True),
    sa.Column("codecarbon_version", sa.String, nullable=True),
    sa.Column("codecarbon_install_method", sa.String, nullable=True),
]

# Columns that existed on the old ``create_all``-generated ``telemetry`` table
# (see ``telemetry_sql_models.py`` on master before this migration) but are not
# part of the new, minimal-level-only model. Dropped on upgrade, restored
# (nullable) on downgrade so no data is lost either way.
OLD_ONLY_COLUMNS = [
    sa.Column("longitude", sa.Float, nullable=True),
    sa.Column("latitude", sa.Float, nullable=True),
    sa.Column("python_executable_hash", sa.String, nullable=True),
    sa.Column("total_emissions_kg", sa.Float, nullable=True),
    sa.Column("emissions_rate_kg_per_sec", sa.Float, nullable=True),
    sa.Column("energy_consumed_kwh", sa.Float, nullable=True),
    sa.Column("cpu_energy_kwh", sa.Float, nullable=True),
    sa.Column("gpu_energy_kwh", sa.Float, nullable=True),
    sa.Column("ram_energy_kwh", sa.Float, nullable=True),
    sa.Column("duration_seconds", sa.Float, nullable=True),
    sa.Column("cpu_utilization_avg", sa.Float, nullable=True),
    sa.Column("gpu_utilization_avg", sa.Float, nullable=True),
    sa.Column("ram_utilization_avg", sa.Float, nullable=True),
    sa.Column("tracking_mode", sa.String, nullable=True),
    sa.Column("api_mode", sa.String, nullable=True),
    sa.Column("output_methods", sa.JSON, nullable=True),
    sa.Column("hardware_tracked", sa.JSON, nullable=True),
    sa.Column("task_tracking_used", sa.Boolean, nullable=True),
    sa.Column("decorator_vs_context", sa.String, nullable=True),
    sa.Column("measure_power_interval_secs", sa.Float, nullable=True),
    sa.Column("hardware_detection_success", sa.Boolean, nullable=True),
    sa.Column("rapl_available", sa.Boolean, nullable=True),
    sa.Column("gpu_detection_method", sa.String, nullable=True),
    sa.Column("first_measurement_time_ms", sa.Float, nullable=True),
    sa.Column("tracking_overhead_percent", sa.Float, nullable=True),
    sa.Column("errors_encountered", sa.JSON, nullable=True),
    sa.Column("warning_count", sa.Integer, nullable=True),
    sa.Column("ide_used", sa.String, nullable=True),
    sa.Column("notebook_environment", sa.String, nullable=True),
    sa.Column("ci_environment", sa.String, nullable=True),
    sa.Column("python_package_manager", sa.String, nullable=True),
    sa.Column("framework_detected", sa.String, nullable=True),
    sa.Column("has_torch", sa.Boolean, nullable=True),
    sa.Column("torch_version", sa.String, nullable=True),
    sa.Column("has_transformers", sa.Boolean, nullable=True),
    sa.Column("transformers_version", sa.String, nullable=True),
    sa.Column("has_diffusers", sa.Boolean, nullable=True),
    sa.Column("diffusers_version", sa.String, nullable=True),
    sa.Column("has_tensorflow", sa.Boolean, nullable=True),
    sa.Column("tensorflow_version", sa.String, nullable=True),
    sa.Column("has_keras", sa.Boolean, nullable=True),
    sa.Column("keras_version", sa.String, nullable=True),
    sa.Column("has_pytorch_lightning", sa.Boolean, nullable=True),
    sa.Column("pytorch_lightning_version", sa.String, nullable=True),
    sa.Column("has_fastai", sa.Boolean, nullable=True),
    sa.Column("fastai_version", sa.String, nullable=True),
    sa.Column("ml_framework_primary", sa.String, nullable=True),
    sa.Column("container_runtime", sa.String, nullable=True),
    sa.Column("in_container", sa.Boolean, nullable=True),
    sa.Column("host_machine_hash", sa.String, nullable=True),
]


def _bind_is_postgres(bind) -> bool:
    """SQLite (used by the migration test) can't ALTER a column's type."""
    return bind.dialect.name == "postgresql"


def _ensure_retention(bind) -> None:
    """Delete telemetry rows older than 3 years, enforced in the database.

    A statement-level trigger fires after every insert and purges rows past
    the retention window, so the policy holds regardless of what the
    application does. The index keeps the purge's WHERE clause a cheap range
    scan. Postgres only; SQLite (used by the migration test) has no trigger.
    """
    if not _bind_is_postgres(bind):
        return
    inspector = sa.inspect(bind)
    existing_indexes = {ix["name"] for ix in inspector.get_indexes("telemetry")}
    if "ix_telemetry_timestamp" not in existing_indexes:
        op.create_index("ix_telemetry_timestamp", "telemetry", ["timestamp"])
    op.execute("""
        CREATE OR REPLACE FUNCTION telemetry_purge() RETURNS trigger AS $$
        BEGIN
            DELETE FROM telemetry WHERE timestamp < now() - interval '3 years';
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """)
    op.execute("DROP TRIGGER IF EXISTS telemetry_retention ON telemetry;")
    op.execute("""
        CREATE TRIGGER telemetry_retention
        AFTER INSERT ON telemetry
        FOR EACH STATEMENT EXECUTE FUNCTION telemetry_purge();
        """)


def upgrade():
    """Anonymous SDK telemetry, one row per process (minimal level only).

    Some production databases already have a ``telemetry`` table, created by
    ``Base.metadata.create_all`` before this migration existed (see #1171),
    with the old wide schema (``latitude``/``longitude``/etc). In that case
    only the schema is adjusted in place, so existing rows are preserved;
    otherwise the table is created fresh.
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("telemetry"):
        existing = {c["name"] for c in inspector.get_columns("telemetry")}
        for column in OLD_ONLY_COLUMNS:
            if column.name in existing:
                op.drop_column("telemetry", column.name)
        for column in NEW_COLUMNS:
            if column.name not in existing:
                op.add_column("telemetry", column.copy())
        if "timestamp" in existing and _bind_is_postgres(bind):
            op.alter_column(
                "telemetry",
                "timestamp",
                type_=sa.DateTime(timezone=True),
                postgresql_using="timestamp AT TIME ZONE 'UTC'",
            )
        _ensure_retention(bind)
        return
    op.create_table(
        "telemetry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        *(column.copy() for column in NEW_COLUMNS),
    )
    op.create_index("ix_telemetry_id", "telemetry", ["id"])
    _ensure_retention(bind)


def downgrade():
    """Restore the old, wider schema (as nullable columns), preserving rows."""
    bind = op.get_bind()
    if _bind_is_postgres(bind):
        op.execute("DROP TRIGGER IF EXISTS telemetry_retention ON telemetry;")
        op.execute("DROP FUNCTION IF EXISTS telemetry_purge();")
        op.execute("DROP INDEX IF EXISTS ix_telemetry_timestamp;")
    existing = {c["name"] for c in sa.inspect(bind).get_columns("telemetry")}
    for column in OLD_ONLY_COLUMNS:
        if column.name not in existing:
            op.add_column("telemetry", column.copy())
    if _bind_is_postgres(bind):
        op.alter_column(
            "telemetry",
            "timestamp",
            type_=sa.DateTime(),
            postgresql_using="timestamp AT TIME ZONE 'UTC'",
        )
