"""seed_dfg_team_data

Revision ID: 73a394753d3a
Revises: 5abae4eb2079
Create Date: 2021-05-20 11:34:59.174223

"""
from alembic import op

ADMIN_ORG_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
DFG_TEAM_ID = "8edb03e1-9a28-452a-9c93-a3b6560136d7"

revision = "73a394753d3a"
down_revision = "5abae4eb2079"
branch_labels = None
depends_on = None


def upgrade():
    data_for_good_team_columns = "(id,name,description,organization_id)"

    data_for_good_team_values = (
        DFG_TEAM_ID,
        "DataForGood",
        "DataForGood Team",
        ADMIN_ORG_ID,
    )
    op.execute(
        "INSERT INTO teams {data_for_good_team_columns} VALUES {data_for_good_team_values}".format(
            data_for_good_team_columns=data_for_good_team_columns,
            data_for_good_team_values=str(data_for_good_team_values),
        )
    )


def downgrade():
    op.execute(
        "DELETE FROM teams WHERE id = '{dfg_team_id}'".format(dfg_team_id=DFG_TEAM_ID)
    )

    pass
