"""add project tokens

Revision ID: caf929e09f7c
Revises: 7ace119b161f
Create Date: 2024-07-25 19:51:43.046273

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "caf929e09f7c"
down_revision = "7ace119b161f"
branch_labels = None
depends_on = None


def upgrade():

    # Create the project_tokens table

    op.create_table(
        "project_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("project_id", UUID(as_uuid=True)),
        sa.Column("token", sa.String, unique=True),
        sa.Column("name", sa.String),
        sa.Column("access", sa.Integer),
        sa.Column("last_used", sa.DateTime, nullable=True),
    )
    # Create the foreign key constraint between the project_tokens and projects tables
    op.create_foreign_key(
        "fk_project_tokens_projects",
        "project_tokens",
        "projects",
        ["project_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        "fk_project_tokens_projects", "project_tokens", type_="foreignkey"
    )
    op.drop_table("project_tokens")
