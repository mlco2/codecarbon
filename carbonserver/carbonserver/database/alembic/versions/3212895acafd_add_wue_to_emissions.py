"""add_wue_to_emissions

Revision ID: 3212895acafd
Revises: 2a898cf81c3e
Create Date: 2025-10-19 21:29:36.800401

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3212895acafd"
down_revision = "2a898cf81c3e"
branch_labels = None
depends_on = None


def upgrade():
    """
    Add WUE (Water Usage Effectiveness) field to emissions table.
    Default value is 0 (no water usage).
    """
    op.add_column(
        "emissions",
        sa.Column("wue", sa.Float, nullable=False, server_default="0"),
    )


def downgrade():
    """
    Remove WUE field from emissions table.
    """
    op.drop_column("emissions", "wue")
