""" add codecarbon version

Revision ID: 298059b19bde
Revises: edcd10edf11d
Create Date: 2022-08-05 18:52:23.199306

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "298059b19bde"
down_revision = "edcd10edf11d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("runs", sa.Column("codecarbon_version", sa.String))


def downgrade():
    op.drop_column("runs", "codecarbon_version")
