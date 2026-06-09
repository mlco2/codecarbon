"""
Integration test for project cascade delete functionality.

This test verifies that when a project is deleted, all related entities
are automatically deleted via CASCADE:
- Experiments
- Runs
- Emissions
- Project Tokens

To run this test:
1. Start the database: docker-compose up -d postgres
2. Run migration: uv run --extra api task setup-db
3. Set environment: export DATABASE_URL=postgresql://codecarbon-user:supersecret@localhost:5432/codecarbon_db
4. Run test: uv run --extra api pytest tests/api/integration/test_project_cascade_delete.py -v
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from carbonserver.api.infra.database.sql_models import (
    Emission,
    Experiment,
    Organization,
    Project,
    ProjectToken,
    Run,
    User,
)
from carbonserver.config import settings


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    engine = create_engine(settings.db_url)
    session = Session(engine)
    yield session
    session.close()


@pytest.fixture
def test_data_cleanup(db_session):
    """Cleanup test data after test execution."""
    test_ids = {
        "org_id": None,
        "user_id": None,
        "project_id": None,
    }

    yield test_ids

    # Cleanup in reverse order of dependencies
    if test_ids["project_id"]:
        db_session.query(Project).filter(Project.id == test_ids["project_id"]).delete()
    if test_ids["org_id"]:
        db_session.query(Organization).filter(
            Organization.id == test_ids["org_id"]
        ).delete()
    if test_ids["user_id"]:
        db_session.query(User).filter(User.id == test_ids["user_id"]).delete()

    db_session.commit()


def test_project_cascade_delete(db_session, test_data_cleanup):
    """
    Test that deleting a project cascades to all child entities.

    This test creates a full hierarchy:
    Organization -> Project -> Experiment -> Run -> Emission
                           \\-> ProjectToken

    Then deletes the project and verifies all children are removed.
    """

    # 1. Setup: Create test organization
    org_id = uuid.uuid4()
    test_org = Organization(
        id=org_id,
        name="Test Cascade Org",
        description="Organization for cascade delete testing",
    )
    db_session.add(test_org)
    db_session.commit()
    test_data_cleanup["org_id"] = org_id

    # 2. Create test project
    project_id = uuid.uuid4()
    test_project = Project(
        id=project_id,
        name="Test Cascade Project",
        description="Project to test cascade delete",
        organization_id=org_id,
    )
    db_session.add(test_project)
    db_session.commit()
    test_data_cleanup["project_id"] = project_id

    # 3. Create experiments
    experiment_1_id = uuid.uuid4()
    experiment_2_id = uuid.uuid4()

    experiment_1 = Experiment(
        id=experiment_1_id,
        timestamp=datetime.now(),
        name="Experiment 1",
        description="First test experiment",
        project_id=project_id,
        country_name="France",
        country_iso_code="FRA",
        region="europe-west",
    )

    experiment_2 = Experiment(
        id=experiment_2_id,
        timestamp=datetime.now(),
        name="Experiment 2",
        description="Second test experiment",
        project_id=project_id,
        country_name="USA",
        country_iso_code="USA",
        region="us-east",
    )

    db_session.add(experiment_1)
    db_session.add(experiment_2)
    db_session.commit()

    # 4. Create runs for each experiment
    run_1_id = uuid.uuid4()
    run_2_id = uuid.uuid4()

    run_1 = Run(
        id=run_1_id,
        timestamp=datetime.now(),
        experiment_id=experiment_1_id,
        os="Linux",
        python_version="3.12.0",
        codecarbon_version="2.0.0",
    )

    run_2 = Run(
        id=run_2_id,
        timestamp=datetime.now(),
        experiment_id=experiment_2_id,
        os="Darwin",
        python_version="3.11.0",
        codecarbon_version="2.0.0",
    )

    db_session.add(run_1)
    db_session.add(run_2)
    db_session.commit()

    # 5. Create emissions for each run
    emission_1_id = uuid.uuid4()
    emission_2_id = uuid.uuid4()
    emission_3_id = uuid.uuid4()

    emission_1 = Emission(
        id=emission_1_id,
        timestamp=datetime.now(),
        run_id=run_1_id,
        duration=100.0,
        emissions_sum=0.5,
        emissions_rate=0.005,
        energy_consumed=1.2,
    )

    emission_2 = Emission(
        id=emission_2_id,
        timestamp=datetime.now(),
        run_id=run_1_id,
        duration=200.0,
        emissions_sum=1.0,
        emissions_rate=0.005,
        energy_consumed=2.4,
    )

    emission_3 = Emission(
        id=emission_3_id,
        timestamp=datetime.now(),
        run_id=run_2_id,
        duration=150.0,
        emissions_sum=0.75,
        emissions_rate=0.005,
        energy_consumed=1.8,
    )

    db_session.add(emission_1)
    db_session.add(emission_2)
    db_session.add(emission_3)
    db_session.commit()

    # 6. Create project tokens
    token_1_id = uuid.uuid4()
    token_2_id = uuid.uuid4()

    token_1 = ProjectToken(
        id=token_1_id,
        project_id=project_id,
        name="Test Token 1",
        hashed_token="hashed_value_1",
        lookup_value="lookup_1",
        access=1,
    )

    token_2 = ProjectToken(
        id=token_2_id,
        project_id=project_id,
        name="Test Token 2",
        hashed_token="hashed_value_2",
        lookup_value="lookup_2",
        access=2,
    )

    db_session.add(token_1)
    db_session.add(token_2)
    db_session.commit()

    # 7. Verify all data exists before deletion
    assert db_session.get(Project, project_id) is not None
    assert db_session.get(Experiment, experiment_1_id) is not None
    assert db_session.get(Experiment, experiment_2_id) is not None
    assert db_session.get(Run, run_1_id) is not None
    assert db_session.get(Run, run_2_id) is not None
    assert db_session.get(Emission, emission_1_id) is not None
    assert db_session.get(Emission, emission_2_id) is not None
    assert db_session.get(Emission, emission_3_id) is not None
    assert db_session.get(ProjectToken, token_1_id) is not None
    assert db_session.get(ProjectToken, token_2_id) is not None

    # Count records
    experiments_count = (
        db_session.query(Experiment).filter(Experiment.project_id == project_id).count()
    )
    runs_count = (
        db_session.query(Run)
        .filter(Run.experiment_id.in_([experiment_1_id, experiment_2_id]))
        .count()
    )
    emissions_count = (
        db_session.query(Emission)
        .filter(Emission.run_id.in_([run_1_id, run_2_id]))
        .count()
    )
    tokens_count = (
        db_session.query(ProjectToken)
        .filter(ProjectToken.project_id == project_id)
        .count()
    )

    assert experiments_count == 2, "Should have 2 experiments"
    assert runs_count == 2, "Should have 2 runs"
    assert emissions_count == 3, "Should have 3 emissions"
    assert tokens_count == 2, "Should have 2 project tokens"

    # 8. DELETE THE PROJECT - This should cascade to all children
    db_session.delete(test_project)
    db_session.commit()

    # Mark as deleted so cleanup doesn't try to delete again
    test_data_cleanup["project_id"] = None

    # 9. Verify CASCADE DELETE worked - all children should be gone
    assert db_session.get(Project, project_id) is None, "Project should be deleted"

    # Experiments should be cascade deleted
    assert (
        db_session.get(Experiment, experiment_1_id) is None
    ), "Experiment 1 should be cascade deleted"
    assert (
        db_session.get(Experiment, experiment_2_id) is None
    ), "Experiment 2 should be cascade deleted"

    # Runs should be cascade deleted
    assert db_session.get(Run, run_1_id) is None, "Run 1 should be cascade deleted"
    assert db_session.get(Run, run_2_id) is None, "Run 2 should be cascade deleted"

    # Emissions should be cascade deleted
    assert (
        db_session.get(Emission, emission_1_id) is None
    ), "Emission 1 should be cascade deleted"
    assert (
        db_session.get(Emission, emission_2_id) is None
    ), "Emission 2 should be cascade deleted"
    assert (
        db_session.get(Emission, emission_3_id) is None
    ), "Emission 3 should be cascade deleted"

    # Project tokens should be cascade deleted
    assert (
        db_session.get(ProjectToken, token_1_id) is None
    ), "Project token 1 should be cascade deleted"
    assert (
        db_session.get(ProjectToken, token_2_id) is None
    ), "Project token 2 should be cascade deleted"

    # Verify counts are zero
    experiments_count_after = (
        db_session.query(Experiment).filter(Experiment.project_id == project_id).count()
    )
    runs_count_after = (
        db_session.query(Run)
        .filter(Run.experiment_id.in_([experiment_1_id, experiment_2_id]))
        .count()
    )
    emissions_count_after = (
        db_session.query(Emission)
        .filter(Emission.run_id.in_([run_1_id, run_2_id]))
        .count()
    )
    tokens_count_after = (
        db_session.query(ProjectToken)
        .filter(ProjectToken.project_id == project_id)
        .count()
    )

    assert experiments_count_after == 0, "All experiments should be deleted"
    assert runs_count_after == 0, "All runs should be deleted"
    assert emissions_count_after == 0, "All emissions should be deleted"
    assert tokens_count_after == 0, "All project tokens should be deleted"

    # 10. Verify parent organization still exists (not affected by cascade)
    assert (
        db_session.get(Organization, org_id) is not None
    ), "Organization should NOT be deleted (cascade only goes down, not up)"


def test_project_delete_via_repository(db_session, test_data_cleanup):
    """
    Test cascade delete through the repository layer (simulating API delete).
    """
    from carbonserver.api.infra.repositories.repository_projects import (
        SqlAlchemyRepository,
    )

    # Create minimal test data
    org_id = uuid.uuid4()
    test_org = Organization(id=org_id, name="Test Repo Org", description="Test")
    db_session.add(test_org)
    db_session.commit()
    test_data_cleanup["org_id"] = org_id

    project_id = uuid.uuid4()
    test_project = Project(
        id=project_id,
        name="Test Repo Project",
        description="Test",
        organization_id=org_id,
    )
    db_session.add(test_project)
    db_session.commit()

    # Add an experiment
    experiment_id = uuid.uuid4()
    experiment = Experiment(
        id=experiment_id,
        timestamp=datetime.now(),
        name="Test Experiment",
        description="Test",
        project_id=project_id,
    )
    db_session.add(experiment)
    db_session.commit()

    # Verify setup
    assert db_session.get(Project, project_id) is not None
    assert db_session.get(Experiment, experiment_id) is not None

    # Delete via repository
    def mock_session_factory():
        return db_session

    repository = SqlAlchemyRepository(session_factory=mock_session_factory)
    repository.delete_project(str(project_id))

    # Verify cascade delete worked
    assert db_session.get(Project, project_id) is None
    assert db_session.get(Experiment, experiment_id) is None
