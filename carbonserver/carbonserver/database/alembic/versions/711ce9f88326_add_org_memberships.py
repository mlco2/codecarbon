"""Add org memberships.

Revision ID: 711ce9f88326
Revises: 951141858cff
Create Date: 2024-08-26 18:17:36.679046

"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "711ce9f88326"
down_revision = "951141858cff"
branch_labels = None
depends_on = None


def upgrade():
    """
    Remove organizations field from User
    Add new many to many relationship with admin flag
    """
    op.drop_constraint("fk_users_organizations", "users", type_="foreignkey")
    op.alter_column("users", "organizations", new_column_name="old_organizations")
    t_memberships = op.create_table(
        "memberships",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("organization_id", "user_id"),
    )

    connection = op.get_bind()
    t_users = sa.Table(
        "users",
        sa.MetaData(),
        sa.Column("id", sa.String(32)),
        sa.Column(
            "old_organizations", sa.ARRAY(sa.String, as_tuple=False, dimensions=1)
        ),
    )

    # get old organizations list from users and migrate to new table
    users_to_migrate = connection.execute(
        sa.select(
            [
                t_users.c.id,
                t_users.c.old_organizations,
            ]
        )
    ).fetchall()
    for user_id, old_organizations in users_to_migrate:
        print("=====", user_id, old_organizations)
        for organization_id in old_organizations:
            print(f"adding {user_id=}, {organization_id=}, is_admin=True")
            connection.execute(
                t_memberships.insert().values(
                    user_id=user_id,
                    organization_id=UUID(organization_id),
                    is_admin=True,
                )
            )

    op.drop_column("users", "old_organizations")


def downgrade():
    op.create_foreign_key(
        "fk_users_organizations", "users", "organizations", ["organization_id"], ["id"]
    )
    op.drop_table("memberships")
    op.add_column(
        "organizations", sa.Column(sa.ARRAY(sa.String, as_tuple=False, dimensions=1))
    )
