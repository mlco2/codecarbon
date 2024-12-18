"""clean users and org rights management
Revision ID: 951141858cff
Revises: 7ace119b161f
Create Date: 2024-07-29 08:40:08.330472
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "951141858cff"
down_revision = "caf929e09f7c"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("users", "hashed_password")
    op.drop_column("users", "api_key")
    op.drop_column("organizations", "api_key")


def downgrade():
    op.add_column("organizations", sa.Column("api_key", sa.String, default=None))
    op.add_column("users", sa.Column("api_key", sa.String, default=None))
    op.add_column("users", sa.Column("hashed_password", sa.String, default=None))
