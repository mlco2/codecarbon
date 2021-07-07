"""seperate cpu and gpu energy values

Revision ID: f12747ed7e9c
Revises: 73a394753d3a
Create Date: 2021-07-07 14:27:19.702460

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f12747ed7e9c'
down_revision = '73a394753d3a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('emissions', sa.Column('cpu_power', sa.Float))
    op.add_column('emissions', sa.Column('gpu_power', sa.Float))


def downgrade():
    op.drop_column('emissions', sa.Column('cpu_power', sa.Float))
    op.drop_column('emissions', sa.Column('gpu_power', sa.Float))
