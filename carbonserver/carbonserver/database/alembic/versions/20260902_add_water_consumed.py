"""add water_consumed to emissions

Revision ID: 20260902_add_water
Revises: 20251119_add_utilization
Create Date: 2026-09-02

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260902_add_water"
down_revision = "20251119_add_utilization"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "emissions",
        sa.Column("water_consumed", sa.Float(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("emissions", "water_consumed")
