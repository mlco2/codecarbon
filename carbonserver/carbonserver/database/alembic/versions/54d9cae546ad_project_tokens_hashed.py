"""project tokens hashed

Revision ID: 54d9cae546ad
Revises: 711ce9f88326
Create Date: 2024-10-15 10:03:34.722490

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "54d9cae546ad"
down_revision = "711ce9f88326"
branch_labels = None
depends_on = None


def upgrade():
    # Remove token column
    op.drop_column("project_tokens", "token")
    # Add hashed_token column
    op.add_column(
        "project_tokens", sa.Column("hashed_token", sa.String(), nullable=False)
    )
    # Add lookup_value column
    op.add_column(
        "project_tokens", sa.Column("lookup_value", sa.String(), nullable=False)
    )
    # Add revoked column
    op.add_column(
        "project_tokens",
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade():
    # Remove revoked column
    op.drop_column("project_tokens", "revoked")
    # Remove lookup_value column
    op.drop_column("project_tokens", "lookup_value")
    # Remove hashed_token column
    op.drop_column("project_tokens", "hashed_token")
    # Add token column
    op.add_column("project_tokens", sa.Column("token", sa.String(), nullable=True))
