"""add_model_benchmarks_table

Standalone table for published LLM energy benchmarks. Deliberately not linked
to runs: see the docstring on sql_models.ModelBenchmark.

Revision ID: 20260808_model_bench
Revises: 20251119_add_utilization
Create Date: 2026-08-08 14:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "20260808_model_bench"
down_revision = "20251119_add_utilization"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "model_benchmarks",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            index=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("submitted_at", sa.DateTime, nullable=False),
        sa.Column(
            "submitted_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("spec_version", sa.String, nullable=False),
        # identity
        sa.Column("model_name", sa.String, nullable=False, index=True),
        sa.Column("model_revision", sa.String, nullable=True),
        sa.Column("quantization", sa.String, nullable=False),
        sa.Column("engine", sa.String, nullable=False),
        sa.Column("engine_version", sa.String, nullable=True),
        # Submitter-chosen deployment identity, so a consumer can select "my
        # box" rather than "some A100". Optional: same-class records are
        # expected to agree.
        sa.Column("deployment_id", sa.String, nullable=True, index=True),
        sa.Column("deployment_label", sa.String, nullable=True),
        # the variables that make results incomparable
        sa.Column("concurrency", sa.Integer, nullable=False, index=True),
        sa.Column("input_token_bucket", sa.Integer, nullable=True),
        sa.Column("gpu_model", sa.String, nullable=True, index=True),
        sa.Column("gpu_count", sa.Integer, nullable=True),
        sa.Column("infra_type", sa.String, nullable=True),
        # raw measurement
        sa.Column("duration", sa.Float, nullable=False),
        sa.Column("it_energy_kwh", sa.Float, nullable=False),
        sa.Column("input_tokens", sa.BigInteger, nullable=True),
        sa.Column("output_tokens", sa.BigInteger, nullable=False),
        # derived server-side
        sa.Column("it_energy_per_token", sa.Float, nullable=False),
        sa.Column("latency_per_token_s", sa.Float, nullable=True),
        sa.Column("record", JSONB, nullable=False),
    )


def downgrade():
    op.drop_table("model_benchmarks")
