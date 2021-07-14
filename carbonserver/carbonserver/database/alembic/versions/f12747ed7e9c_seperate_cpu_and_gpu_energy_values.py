"""seperate cpu and gpu energy values

Revision ID: f12747ed7e9c
Revises: 73a394753d3a
Create Date: 2021-07-07 14:27:19.702460

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f12747ed7e9c"
down_revision = "73a394753d3a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("emissions", sa.Column("cpu_power", sa.Float))
    op.add_column("emissions", sa.Column("gpu_power", sa.Float))
    op.add_column("emissions", sa.Column("ram_power", sa.Float))
    op.add_column("emissions", sa.Column("cpu_energy", sa.Float))
    op.add_column("emissions", sa.Column("gpu_energy", sa.Float))
    op.add_column("emissions", sa.Column("ram_energy", sa.Float))


def downgrade():
    op.drop_column("emissions", "cpu_power")
    op.drop_column("emissions", "gpu_power")
    op.drop_column("emissions", "ram_power")
    op.drop_column("emissions", "cpu_energy")
    op.drop_column("emissions", "gpu_energy")
    op.drop_column("emissions", "ram_energy")
