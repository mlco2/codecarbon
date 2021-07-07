"""create_tables stateless script

Revision ID: 5abae4eb2079
Revises: None
Create Date: 2021-05-18 22:21:49.659708

"""
import os
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine.reflection import Inspector

ADMIN_ORG_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"

ADMIN_TEAM_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
ADMIN_TEAM_API_KEY = os.environ.get("ADMIN_TEAM_API_KEY", "supersecret")


COMMUNITY_ORG_ID = "e52fe339-164d-4c2b-a8c0-f562dfce066d"
COMMUNITY_ORG_API_KEY = "default"

DFG_TEAM_ID = "8edb03e1-9a28-452a-9c93-a3b6560136d7"
DFG_TEAM_API_KEY = "default"

revision = "5abae4eb2079"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Initial creation: removes all code carbon related tables & creates them with initial user / organization / team.
    """

    downgrade()

    op.create_table(
        "emissions",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
        ),
        sa.Column("timestamp", sa.DateTime),
        sa.Column("duration", sa.Float),
        sa.Column("emissions", sa.Float),
        sa.Column("energy_consumed", sa.Float),
        sa.Column("run_id", UUID(as_uuid=True)),
        keep_existing=False,
    )

    op.create_table(
        "runs",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
        ),
        sa.Column("timestamp", sa.DateTime),
        sa.Column("experiment_id", UUID(as_uuid=True)),
        keep_existing=False,
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
        sa.Column("project_id", UUID(as_uuid=True)),
        keep_existing=False,
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
        sa.Column("team_id", UUID(as_uuid=True)),
        keep_existing=False,
    )

    op.create_foreign_key(
        "fk_experiments_projects", "experiments", "projects", ["project_id"], ["id"]
    )

    teams = op.create_table(
        "teams",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
        ),
        sa.Column("name", sa.String),
        sa.Column("description", sa.String),
        sa.Column("api_key", sa.String),
        sa.Column("organization_id", UUID(as_uuid=True)),
        keep_existing=False,
    )

    op.create_foreign_key("fk_projects_teams", "projects", "teams", ["team_id"], ["id"])

    organizations = op.create_table(
        "organizations",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
        ),
        sa.Column("name", sa.String),
        sa.Column("description", sa.String),
        sa.Column("api_key", sa.String),
        sa.Column("teams", sa.types.ARRAY(sa.String, as_tuple=False, dimensions=1)),
        keep_existing=False,
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
        sa.Column("teams", sa.types.ARRAY(sa.String, as_tuple=False, dimensions=1)),
        sa.Column(
            "organizations", sa.types.ARRAY(sa.String, as_tuple=False, dimensions=1)
        ),
        sa.Column("organization_id", UUID(as_uuid=True)),
        keep_existing=False,
    )

    op.create_foreign_key(
        "fk_users_organizations", "users", "organizations", ["organization_id"], ["id"]
    )

    op.bulk_insert(
        organizations,
        [
            {
                "id": ADMIN_ORG_ID,
                "name": "admin",
                "description": "Administration organization",
                "api_key": ADMIN_TEAM_API_KEY,
            },
            {
                "id": COMMUNITY_ORG_ID,
                "name": "Community organization",
                "description": "Community organization",
                "api_key": COMMUNITY_ORG_API_KEY,
            },
        ],
    )

    op.bulk_insert(
        teams,
        [
            {
                "id": ADMIN_TEAM_ID,
                "name": "admin",
                "description": "Administration team",
                "api_key": ADMIN_TEAM_API_KEY,
                "organization_id": ADMIN_ORG_ID,
            }
        ],
    )


def downgrade():
    """
    Check if tables exists, and then removes them
    """

    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    sql_tables = inspector.get_table_names()
    tables = [
        "emissions",
        "runs",
        "experiments",
        "projects",
        "teams",
        "users",
        "organizations",
    ]
    for t in tables:
        if t in sql_tables:
            op.drop_table(t)
