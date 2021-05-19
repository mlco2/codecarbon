"""create_tables

Revision ID: 5abae4eb2079
Revises: Tables creation
Create Date: 2021-05-18 22:21:49.659708

"""
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "5abae4eb2079"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Create all tables
    """
    op.create_table(
        "emissions",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
        ),
        sa.Column("timestamp", sa.DateTime),
        sa.Column("duration", sa.Float),
        sa.Column("emissions", sa.Float),
        sa.Column("energy_consumed", sa.Float),
        sa.Column("run_id", UUID),
    )

    op.create_table(
        "runs",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
        ),
        sa.Column("timestamp", sa.DateTime),
        sa.Column("experiment_id", UUID),
    )

    op.create_foreign_key("fk_emissions_runs", "emissions", "runs", ["run_id"], ["id"])

    op.create_table(
        "experiments",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
        ),
        sa.Column("timestamp", sa.DateTime),
        sa.Column("name", sa.String),
        sa.Column("description", sa.String),
        sa.Column("country_name", sa.String),
        sa.Column("country_iso_code", sa.String),
        sa.Column("region", sa.String),
        sa.Column("on_cloud", sa.Boolean, default=False),
        sa.Column("cloud_provider", sa.String),
        sa.Column("cloud_region", sa.String),
        sa.Column("project_id", UUID),
    )

    op.create_foreign_key(
        "fk_runs_experiments", "runs", "experiments", ["experiment_id"], ["id"]
    )

    op.create_table(
        "projects",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
        ),
        sa.Column("name", sa.String),
        sa.Column("description", sa.String),
        sa.Column("team_id", UUID),
    )

    op.create_foreign_key(
        "fk_experiments_projects", "experiments", "projects", ["project_id"], ["id"]
    )

    op.create_table(
        "teams",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
        ),
        sa.Column("name", sa.String),
        sa.Column("description", sa.String),
        sa.Column("organization_id", UUID),
    )

    op.create_foreign_key("fk_projects_teams", "projects", "teams", ["team_id"], ["id"])

    op.create_table(
        "organizations",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
        ),
        sa.Column("name", sa.String),
        sa.Column("description", sa.String),
    )

    op.create_foreign_key(
        "fk_teams_organizations", "teams", "organizations", ["organization_id"], ["id"]
    )

    op.create_table(
        "users",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
        ),
        sa.Column("name", sa.String),
        sa.Column("api_key", sa.String),
        sa.Column("email", sa.String, unique=True, index=True),
        sa.Column("hashed_password", sa.String),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("organization_id", UUID),
    )

    op.create_foreign_key(
        "fk_users_organizations", "users", "organizations", ["organization_id"], ["id"]
    )


def downgrade():
    """
    Remove all tables
    """
    tables = [
        "emissions",
        "runs",
        "experiments",
        "projects",
        "teams",
        "organizations",
        "users",
    ]
    for t in tables:
        op.drop_table(t)
