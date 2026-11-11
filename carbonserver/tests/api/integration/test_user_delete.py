"""
Integration test for deleting a user account (DELETE /users/me).

Checks against a real database that erasing a user removes the organizations
only they belong to, with everything under them, and leaves organizations
shared with other members untouched.

To run this test:
1. Start the database: docker-compose up -d postgres
2. Run migration: uv run --extra api task setup-db
3. Set environment: export DATABASE_URL=postgresql://codecarbon-user:supersecret@localhost:5432/codecarbon_db
4. Run test: uv run --extra api pytest tests/api/integration/test_user_delete.py -v
"""

import uuid
from contextlib import contextmanager
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from carbonserver.api.infra.database.sql_models import (
    Emission,
    Experiment,
    Membership,
    Organization,
    Project,
    ProjectToken,
    Run,
    User,
)
from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.config import settings


@pytest.fixture
def engine():
    engine = create_engine(settings.db_url)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(engine):
    session = Session(engine)
    yield session
    session.close()


@pytest.fixture
def repository(engine):
    @contextmanager
    def session_factory():
        with Session(engine) as session:
            yield session

    return SqlAlchemyRepository(session_factory)


def add_project_tree(session, org_id):
    """Project -> Experiment -> Run -> Emission, plus an API token."""
    ids = {k: uuid.uuid4() for k in ("project", "experiment", "run", "emission")}
    ids["token"] = uuid.uuid4()
    session.add(Project(id=ids["project"], name="p", organization_id=org_id))
    session.flush()
    session.add(
        Experiment(
            id=ids["experiment"],
            name="e",
            timestamp=datetime.now(),
            project_id=ids["project"],
        )
    )
    session.flush()
    session.add(
        Run(id=ids["run"], timestamp=datetime.now(), experiment_id=ids["experiment"])
    )
    session.flush()
    session.add(
        Emission(id=ids["emission"], timestamp=datetime.now(), run_id=ids["run"])
    )
    session.add(
        ProjectToken(
            id=ids["token"],
            project_id=ids["project"],
            name="t",
            hashed_token="h",
            lookup_value="l",
        )
    )
    session.commit()
    return ids


@pytest.fixture
def accounts(db_session):
    """Leaving user with a solo org and a shared org; a colleague who stays."""
    leaving_id, colleague_id = uuid.uuid4(), uuid.uuid4()
    solo_org_id, shared_org_id = uuid.uuid4(), uuid.uuid4()
    db_session.add_all(
        [
            User(id=leaving_id, name="Leaving", email=f"{leaving_id}@example.org"),
            User(id=colleague_id, name="Stays", email=f"{colleague_id}@example.org"),
            Organization(id=solo_org_id, name="solo"),
            Organization(id=shared_org_id, name="shared"),
        ]
    )
    db_session.flush()
    db_session.add_all(
        [
            Membership(user_id=leaving_id, organization_id=solo_org_id, is_admin=True),
            Membership(
                user_id=leaving_id, organization_id=shared_org_id, is_admin=True
            ),
            Membership(
                user_id=colleague_id, organization_id=shared_org_id, is_admin=False
            ),
        ]
    )
    db_session.commit()
    data = {
        "leaving_id": leaving_id,
        "colleague_id": colleague_id,
        "solo_org_id": solo_org_id,
        "shared_org_id": shared_org_id,
        "solo_tree": add_project_tree(db_session, solo_org_id),
        "shared_tree": add_project_tree(db_session, shared_org_id),
    }

    yield data

    db_session.rollback()
    db_session.query(Project).filter(
        Project.organization_id.in_([solo_org_id, shared_org_id])
    ).delete(synchronize_session=False)
    db_session.query(Membership).filter(
        Membership.user_id.in_([leaving_id, colleague_id])
    ).delete(synchronize_session=False)
    db_session.query(Organization).filter(
        Organization.id.in_([solo_org_id, shared_org_id])
    ).delete(synchronize_session=False)
    db_session.query(User).filter(User.id.in_([leaving_id, colleague_id])).delete(
        synchronize_session=False
    )
    db_session.commit()


def exists(session, model, id_):
    return session.get(model, id_) is not None


def test_delete_user_erases_solo_orgs_and_keeps_shared_ones(
    repository, db_session, accounts
):
    deleted = repository.delete_user(accounts["leaving_id"])

    assert deleted == [accounts["solo_org_id"]]
    db_session.expire_all()

    assert not exists(db_session, User, accounts["leaving_id"])
    assert (
        db_session.query(Membership)
        .filter(Membership.user_id == accounts["leaving_id"])
        .count()
        == 0
    )
    solo = accounts["solo_tree"]
    assert not exists(db_session, Organization, accounts["solo_org_id"])
    assert not exists(db_session, Project, solo["project"])
    assert not exists(db_session, Experiment, solo["experiment"])
    assert not exists(db_session, Run, solo["run"])
    assert not exists(db_session, Emission, solo["emission"])
    assert not exists(db_session, ProjectToken, solo["token"])

    shared = accounts["shared_tree"]
    assert exists(db_session, User, accounts["colleague_id"])
    assert exists(db_session, Organization, accounts["shared_org_id"])
    assert exists(db_session, Project, shared["project"])
    assert exists(db_session, Emission, shared["emission"])
    assert exists(db_session, ProjectToken, shared["token"])
    assert db_session.get(
        Membership,
        (accounts["shared_org_id"], accounts["colleague_id"]),
    )


def test_delete_user_twice_is_a_no_op(repository, accounts):
    repository.delete_user(accounts["leaving_id"])

    assert repository.delete_user(accounts["leaving_id"]) == []
