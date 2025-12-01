"""add metadata in run table

Revision ID: edcd10edf11d
Revises: f12747ed7e9c
Create Date: 2021-09-16 11:37:16.502609

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "edcd10edf11d"
down_revision = "f12747ed7e9c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("runs", sa.Column("os", sa.String))
    op.add_column("runs", sa.Column("python_version", sa.String))
    op.add_column("runs", sa.Column("cpu_count", sa.Integer))
    op.add_column("runs", sa.Column("cpu_model", sa.String))
    op.add_column("runs", sa.Column("gpu_count", sa.Integer))
    op.add_column("runs", sa.Column("gpu_model", sa.String))
    op.add_column("runs", sa.Column("longitude", sa.Float))
    op.add_column("runs", sa.Column("latitude", sa.Float))
    op.add_column("runs", sa.Column("region", sa.String))
    op.add_column("runs", sa.Column("provider", sa.String))
    op.add_column("runs", sa.Column("ram_total_size", sa.Float))
    op.add_column("runs", sa.Column("tracking_mode", sa.String))


def downgrade():
    op.drop_column("runs", "os")
    op.drop_column("runs", "python_version")
    op.drop_column("runs", "cpu_count")
    op.drop_column("runs", "cpu_model")
    op.drop_column("runs", "gpu_count")
    op.drop_column("runs", "gpu_model")
    op.drop_column("runs", "longitude")
    op.drop_column("runs", "latitude")
    op.drop_column("runs", "region")
    op.drop_column("runs", "provider")
    op.drop_column("runs", "ram_total_size")
    op.drop_column("runs", "tracking_mode")
