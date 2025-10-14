"""add_cascade_delete_for_projects

Revision ID: 2a898cf81c3e
Revises: f3a10c95079f
Create Date: 2025-10-05 11:40:28.037992

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2a898cf81c3e"
down_revision = "f3a10c95079f"
branch_labels = None
depends_on = None


def upgrade():
    """
    Add CASCADE delete behavior to foreign keys in the project hierarchy.

    When a Project is deleted, this will automatically delete:
    - All Experiments belonging to that project
    - All Runs belonging to those experiments
    - All Emissions belonging to those runs
    - All ProjectTokens belonging to that project
    """

    # 1. Add CASCADE delete to emissions.run_id foreign key
    # Drop existing constraint (using the name from initial migration)
    op.drop_constraint("fk_emissions_runs", "emissions", type_="foreignkey")
    # Recreate with CASCADE
    op.create_foreign_key(
        "fk_emissions_runs", "emissions", "runs", ["run_id"], ["id"], ondelete="CASCADE"
    )

    # 2. Add CASCADE delete to runs.experiment_id foreign key
    op.drop_constraint("fk_runs_experiments", "runs", type_="foreignkey")
    op.create_foreign_key(
        "fk_runs_experiments",
        "runs",
        "experiments",
        ["experiment_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 3. Add CASCADE delete to experiments.project_id foreign key
    op.drop_constraint("fk_experiments_projects", "experiments", type_="foreignkey")
    op.create_foreign_key(
        "fk_experiments_projects",
        "experiments",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 4. Add CASCADE delete to project_tokens.project_id foreign key
    op.drop_constraint(
        "fk_project_tokens_projects", "project_tokens", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_project_tokens_projects",
        "project_tokens",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    """
    Remove CASCADE delete behavior from foreign keys.
    This restores the original behavior where deleting a project with
    child records will fail with a foreign key constraint violation.
    """

    # 4. Remove CASCADE from project_tokens.project_id
    op.drop_constraint(
        "fk_project_tokens_projects", "project_tokens", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_project_tokens_projects",
        "project_tokens",
        "projects",
        ["project_id"],
        ["id"],
    )

    # 3. Remove CASCADE from experiments.project_id
    op.drop_constraint("fk_experiments_projects", "experiments", type_="foreignkey")
    op.create_foreign_key(
        "fk_experiments_projects", "experiments", "projects", ["project_id"], ["id"]
    )

    # 2. Remove CASCADE from runs.experiment_id
    op.drop_constraint("fk_runs_experiments", "runs", type_="foreignkey")
    op.create_foreign_key(
        "fk_runs_experiments", "runs", "experiments", ["experiment_id"], ["id"]
    )

    # 1. Remove CASCADE from emissions.run_id
    op.drop_constraint("fk_emissions_runs", "emissions", type_="foreignkey")
    op.create_foreign_key("fk_emissions_runs", "emissions", "runs", ["run_id"], ["id"])
