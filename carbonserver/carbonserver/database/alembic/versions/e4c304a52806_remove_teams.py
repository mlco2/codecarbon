"""remove teams and all their relationships

Revision ID: e4c304a52806
Revises: 298059b19bde
Create Date: 2024-06-15 16:45:06.010531

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "e4c304a52806"
down_revision = "298059b19bde"
branch_labels = None
depends_on = None


def upgrade():
    # Delete the relationship between projects and teams
    op.drop_column("projects", "team_id")
    # Delete the relationship between organizations and teams
    op.drop_column("organizations", "teams")
    # Delete the teams field in the table users
    op.drop_column("users", "teams")
    # Delete the table teams
    op.drop_table("teams")


def downgrade():

    # Create the table teams
    op.create_table(
        "teams",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            index=True,
            server_default=sa.text("(gen_random_uuid())"),
        ),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=True,
        ),
        sa.Column("api_key", sa.String(), nullable=True),
    )
    # Add back the team_id column in the projects table and establish a foreign key constraint
    op.add_column(
        "projects",
        sa.Column(
            "team_id", UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=True
        ),
    )

    # Add back the teams column in the organizations table
    op.add_column(
        "organizations",
        sa.Column(
            "teams",
            sa.ARRAY(sa.String, as_tuple=False, dimensions=1),
            nullable=True,
        ),
    )
    # Add back the teams column in the users table
    op.add_column(
        "users",
        sa.Column(
            "teams",
            sa.ARRAY(sa.String, as_tuple=False, dimensions=1),
            nullable=True,
        ),
    )
