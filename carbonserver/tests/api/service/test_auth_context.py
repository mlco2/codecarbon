from unittest import mock
from uuid import UUID

import pytest

from carbonserver.api.infra.repositories.repository_experiments import (
    SqlAlchemyRepository as ExperimentRepository,
)
from carbonserver.api.infra.repositories.repository_projects import (
    SqlAlchemyRepository as ProjectRepository,
)
from carbonserver.api.infra.repositories.repository_runs import (
    SqlAlchemyRepository as RunRepository,
)
from carbonserver.api.infra.repositories.repository_users import (
    SqlAlchemyRepository as UserRepository,
)
from carbonserver.api.schemas import User
from carbonserver.api.services.auth_context import AuthContext

# Test Constants
TEST_USER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
TEST_PROJECT_ID = UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d")
TEST_ORG_ID = UUID("e60afa92-17b7-4720-91a0-1ae91e409ba1")
TEST_EXPERIMENT_ID = UUID("b4e18750-3721-4131-9e13-603a8b89e73f")
TEST_RUN_ID = UUID("c13e851f-5c2f-403d-98d0-51fe15df3bc3")

TEST_USER = User(
    id=TEST_USER_ID, email="test@test.com", name="Test User", is_active=True
)


@pytest.fixture
def auth_context():
    user_repo_mock = mock.Mock(spec=UserRepository)
    project_repo_mock = mock.Mock(spec=ProjectRepository)
    experiment_repo_mock = mock.Mock(spec=ExperimentRepository)
    run_repo_mock = mock.Mock(spec=RunRepository)

    return (
        AuthContext(
            user_repository=user_repo_mock,
            project_repository=project_repo_mock,
            experiment_repository=experiment_repo_mock,
            run_repository=run_repo_mock,
        ),
        user_repo_mock,
        project_repo_mock,
        experiment_repo_mock,
        run_repo_mock,
    )


def test_is_operation_authorized_on_org(auth_context):
    context, user_repo_mock, *_ = auth_context
    user_repo_mock.is_user_in_organization.return_value = True

    result = context.isOperationAuthorizedOnOrg(TEST_ORG_ID, TEST_USER)

    assert result is True
    user_repo_mock.is_user_in_organization.assert_called_once_with(
        organization_id=TEST_ORG_ID, user=TEST_USER
    )


def test_is_operation_authorized_on_project(auth_context):
    context, user_repo_mock, *_ = auth_context
    user_repo_mock.is_user_authorized_on_project.return_value = True

    result = context.isOperationAuthorizedOnProject(TEST_PROJECT_ID, TEST_USER)

    assert result is True
    user_repo_mock.is_user_authorized_on_project.assert_called_once_with(
        TEST_PROJECT_ID, TEST_USER.id
    )


def test_can_read_public_project(auth_context):
    context, _, project_repo_mock, *_ = auth_context
    project_repo_mock.is_project_public.return_value = True

    result = context.can_read_project(TEST_PROJECT_ID, None)

    assert result is True
    project_repo_mock.is_project_public.assert_called_once_with(TEST_PROJECT_ID)


def test_can_read_private_project_with_auth(auth_context):
    context, user_repo_mock, project_repo_mock, *_ = auth_context
    project_repo_mock.is_project_public.return_value = False
    user_repo_mock.is_user_authorized_on_project.return_value = True

    result = context.can_read_project(TEST_PROJECT_ID, TEST_USER)

    assert result is True
    user_repo_mock.is_user_authorized_on_project.assert_called_once_with(
        TEST_PROJECT_ID, TEST_USER.id
    )


def test_can_read_private_project_without_auth(auth_context):
    context, _, project_repo_mock, *_ = auth_context
    project_repo_mock.is_project_public.return_value = False

    with pytest.raises(Exception) as exc:
        context.can_read_project(TEST_PROJECT_ID, None)

    assert exc.value.detail == "Not authenticated"


def test_can_read_organization(auth_context):
    context, user_repo_mock, *_ = auth_context
    user_repo_mock.is_user_in_organization.return_value = True

    result = context.can_read_organization(TEST_ORG_ID, TEST_USER)

    assert result is True
    user_repo_mock.is_user_in_organization.assert_called_once_with(
        organization_id=TEST_ORG_ID, user=TEST_USER
    )


def test_can_write_organization(auth_context):
    context, user_repo_mock, *_ = auth_context
    user_repo_mock.is_admin_in_organization.return_value = True

    result = context.can_write_organization(TEST_ORG_ID, TEST_USER)

    assert result is True
    user_repo_mock.is_admin_in_organization.assert_called_once_with(
        organization_id=TEST_ORG_ID, user=TEST_USER
    )


def test_can_read_experiment_resolves_to_owning_project(auth_context):
    context, user_repo_mock, project_repo_mock, experiment_repo_mock, *_ = auth_context
    experiment_repo_mock.get_one_experiment.return_value = mock.Mock(
        project_id=TEST_PROJECT_ID
    )
    project_repo_mock.is_project_public.return_value = False
    user_repo_mock.is_user_authorized_on_project.return_value = True

    result = context.can_read_experiment(TEST_EXPERIMENT_ID, TEST_USER)

    assert result is True
    experiment_repo_mock.get_one_experiment.assert_called_once_with(TEST_EXPERIMENT_ID)
    user_repo_mock.is_user_authorized_on_project.assert_called_once_with(
        TEST_PROJECT_ID, TEST_USER.id
    )


def test_can_read_run_resolves_through_experiment_to_project(auth_context):
    (
        context,
        _,
        project_repo_mock,
        experiment_repo_mock,
        run_repo_mock,
    ) = auth_context
    run_repo_mock.get_one_run.return_value = mock.Mock(experiment_id=TEST_EXPERIMENT_ID)
    experiment_repo_mock.get_one_experiment.return_value = mock.Mock(
        project_id=TEST_PROJECT_ID
    )
    # A public owning project makes the run readable even for an anonymous user.
    project_repo_mock.is_project_public.return_value = True

    result = context.can_read_run(TEST_RUN_ID, None)

    assert result is True
    run_repo_mock.get_one_run.assert_called_once_with(TEST_RUN_ID)
