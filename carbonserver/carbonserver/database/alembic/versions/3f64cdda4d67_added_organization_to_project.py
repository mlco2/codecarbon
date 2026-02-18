"""Added organization to project

Revision ID: 3f64cdda4d67
Revises: 951141858cff
Create Date: 2024-06-16 22:27:43.746807

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "3f64cdda4d67"
down_revision = "298059b19bde"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "projects",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_projects_organizations",
        "projects",
        "organizations",
        ["organization_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("fk_projects_organizations", "projects", type_="foreignkey")
    op.drop_column("projects", "organization_id")
