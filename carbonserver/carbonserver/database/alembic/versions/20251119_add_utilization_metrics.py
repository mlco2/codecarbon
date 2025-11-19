"""add_utilization_metrics_to_emissions

Revision ID: 20251119_add_utilization
Revises: 202501_f3a10
Create Date: 2025-11-19 18:52:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251119_add_utilization"
down_revision = "202501_f3a10"
branch_labels = None
depends_on = None


def upgrade():
    """
    Add CPU, GPU, and RAM utilization percentage fields to emissions table.
    These fields track the average utilization of resources during emission tracking.
    """
    op.add_column(
        "emissions",
        sa.Column("cpu_utilization_percent", sa.Float, nullable=True),
    )
    op.add_column(
        "emissions",
        sa.Column("gpu_utilization_percent", sa.Float, nullable=True),
    )
    op.add_column(
        "emissions",
        sa.Column("ram_utilization_percent", sa.Float, nullable=True),
    )


def downgrade():
    """
    Remove CPU, GPU, and RAM utilization percentage fields from emissions table.
    """
    op.drop_column("emissions", "ram_utilization_percent")
    op.drop_column("emissions", "gpu_utilization_percent")
    op.drop_column("emissions", "cpu_utilization_percent")
