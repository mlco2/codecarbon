"""create tables

Revision ID: b7037ddec60c
Revises:
Create Date: 2021-05-09 08:44:29.554956

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b7037ddec60c"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Create all tables
    """
    op.create_table(
        "emissions",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("timestamp", sa.DateTime),
        sa.Column("duration", sa.Float),
        sa.Column("emissions", sa.Float),
        sa.Column("energy_consumed", sa.Float),
        # TODO: Add RAM and CPU consumption
        sa.Column(
            "run_id",
            sa.Integer,
            sa.ForeignKey("runs.id"),
        ),
    )

    op.create_table(
        "runs",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("timestamp", sa.DateTime),
        sa.Column(
            "experiment_id",
            sa.Integer,
            sa.ForeignKey("experiments.id"),
        ),
    )

    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("timestamp", sa.DateTime),
        sa.Column("name", sa.String),
        sa.Column("description", sa.String),
        sa.Column("country_name", sa.String),
        sa.Column("country_iso_code", sa.String),
        sa.Column("region", sa.String),
        sa.Column("on_cloud", sa.Boolean, default=False),
        sa.Column("cloud_provider", sa.String),
        sa.Column("cloud_region", sa.String),
        # TODO: Add RAM, GPU and CPU models and size
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id"),
        ),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String),
        sa.Column("description", sa.String),
        sa.Column(
            "team_id",
            sa.Integer,
            sa.ForeignKey("teams.id"),
        ),
    )

    op.create_table(
        "teams",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String),
        sa.Column("description", sa.String),
        sa.Column(
            "organization_id",
            sa.Integer,
            sa.ForeignKey("organizations.id"),
        ),
    )

    # Organization
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String),
        sa.Column("description", sa.String),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String),
        sa.Column("api_key", sa.String),
        sa.Column("email", sa.String, unique=True, index=True),
        sa.Column("hashed_password", sa.String),
        sa.Column("is_active", sa.Boolean, default=True),
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
