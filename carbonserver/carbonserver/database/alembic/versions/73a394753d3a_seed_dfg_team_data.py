"""seed_dfg_team_data

Revision ID: 73a394753d3a
Revises: 5abae4eb2079
Create Date: 2021-05-20 11:34:59.174223

"""

from alembic import op

DFG_ORG_ID = "e52fe339-164d-4c2b-a8c0-f562dfce066d"

DFG_TEAM_ID = "8edb03e1-9a28-452a-9c93-a3b6560136d7"
DFG_TEAM_API_KEY = "default"

DFG_PROJECT_ID = "e60afa92-17b7-4720-91a0-1ae91e409ba1"

revision = "73a394753d3a"
down_revision = "5abae4eb2079"
branch_labels = None
depends_on = None


def upgrade():
    data_for_good_team_columns = "(id,name,description,api_key,organization_id)"
    data_for_good_team_values = (
        DFG_TEAM_ID,
        "DataForGood",
        "DataForGood Team",
        DFG_TEAM_API_KEY,
        DFG_ORG_ID,
    )
    op.execute(
        "INSERT INTO teams {data_for_good_team_columns} VALUES {data_for_good_team_values}".format(
            data_for_good_team_columns=data_for_good_team_columns,
            data_for_good_team_values=str(data_for_good_team_values),
        )
    )

    data_for_good_project_columns = "(id,name,description,team_id)"
    data_for_good_project_values = (
        DFG_PROJECT_ID,
        "DataForGood",
        "DataForGood Project",
        DFG_TEAM_ID,
    )
    op.execute(
        f"INSERT INTO projects {data_for_good_project_columns} VALUES {data_for_good_project_values}"
    )


def downgrade():
    op.execute(
        "DELETE FROM teams WHERE id = '{dfg_team_id}'".format(dfg_team_id=DFG_TEAM_ID)
    )
    op.execute(f"DELETE FROM projects WHERE id = '{DFG_PROJECT_ID}'")
