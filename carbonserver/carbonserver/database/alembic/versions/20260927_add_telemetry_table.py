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


def upgrade():
    """Anonymous SDK telemetry, one row per process (minimal level only)."""
    op.create_table(
        "telemetry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
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
    )
    op.create_index("ix_telemetry_id", "telemetry", ["id"])


def downgrade():
    op.drop_index("ix_telemetry_id", table_name="telemetry")
    op.drop_table("telemetry")
