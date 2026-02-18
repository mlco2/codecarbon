from unittest import mock
from uuid import UUID

from api.mocks import DUMMY_USER, FakeAuthContext

from carbonserver.api.infra.repositories.repository_projects import SqlAlchemyRepository
from carbonserver.api.schemas import Project, ProjectCreate
from carbonserver.api.services.project_service import ProjectService

PROJECT_ID = UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d")

ORGANIZATION_ID = UUID("e60afa92-17b7-4720-91a0-1ae91e409ba1")

PROJECT = Project(
    id=PROJECT_ID,
    name="Project",
    description="Description",
    organization_id=ORGANIZATION_ID,
)


@mock.patch("uuid.uuid4", return_value=PROJECT_ID)
def test_project_service_creates_correct_project(_):
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_id = PROJECT_ID
    project_service: ProjectService = ProjectService(
        repository_mock, auth_context=FakeAuthContext()
    )
    repository_mock.add_project.return_value = PROJECT

    project_to_create = ProjectCreate(
        name="Project",
        description="Description",
        organization_id=ORGANIZATION_ID,
    )

    actual_saved_project_id = project_service.add_project(project_to_create, DUMMY_USER)

    assert actual_saved_project_id.id == expected_id


def test_project_service_deletes_correct_project():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_service: ProjectService = ProjectService(repository_mock, FakeAuthContext())
    repository_mock.delete_project.return_value = None

    project_service.delete_project(PROJECT_ID, DUMMY_USER)

    # Check that the repository delete_project method was called with the correct project_id
    repository_mock.delete_project.assert_called_once_with(PROJECT_ID)


def test_project_service_delete_with_cascade():
    """
    Test that project service delete calls repository delete method.
    The cascade delete to experiments, runs, emissions, and tokens
    is handled at the database level via foreign key constraints.
    """
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_service: ProjectService = ProjectService(repository_mock, FakeAuthContext())
    repository_mock.delete_project.return_value = None

    # Delete the project
    result = project_service.delete_project(PROJECT_ID, DUMMY_USER)

    # Verify repository delete was called
    repository_mock.delete_project.assert_called_once_with(PROJECT_ID)

    # Service should return None for successful delete
    assert result is None


def test_project_service_delete_unauthorized_user():
    """
    Test that deleting a project with an unauthorized user raises an error.
    """
    from carbonserver.api.errors import NotAllowedError, UserException

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)

    # Create an auth context that denies the operation
    class UnauthorizedAuthContext:
        @staticmethod
        def isOperationAuthorizedOnProject(*args, **kwargs):
            return False

    project_service: ProjectService = ProjectService(
        repository_mock, UnauthorizedAuthContext()
    )

    # Attempting to delete should raise UserException
    try:
        project_service.delete_project(PROJECT_ID, DUMMY_USER)
        raise AssertionError("Should have raised UserException")
    except UserException as e:
        # Verify it's the correct error
        assert isinstance(e.error, NotAllowedError)
        assert "Cannot remove project" in e.error.message

    # Repository delete should NOT have been called
    repository_mock.delete_project.assert_not_called()


def test_project_service_delete_nonexistent_project():
    """
    Test that attempting to delete a non-existent project propagates the error.
    """
    from carbonserver.api.errors import NotFoundError, NotFoundErrorEnum, UserException

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_service: ProjectService = ProjectService(repository_mock, FakeAuthContext())

    # Repository raises NotFound error
    repository_mock.delete_project.side_effect = UserException(
        NotFoundError(
            code=NotFoundErrorEnum.NOT_FOUND, message=f"Project not found: {PROJECT_ID}"
        )
    )

    # Service should propagate the exception
    try:
        project_service.delete_project(PROJECT_ID, DUMMY_USER)
        raise AssertionError("Should have raised UserException")
    except UserException as e:
        assert isinstance(e.error, NotFoundError)
        assert "Project not found" in e.error.message


def test_project_service_patches_correct_project():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_service: ProjectService = ProjectService(
        repository_mock, auth_context=FakeAuthContext()
    )
    repository_mock.patch_project.return_value = PROJECT

    actual_saved_project = project_service.patch_project(
        PROJECT_ID, PROJECT, DUMMY_USER
    )

    assert actual_saved_project.id == PROJECT.id
    assert actual_saved_project.name == PROJECT.name
    assert actual_saved_project.description == PROJECT.description
    assert actual_saved_project.organization_id == PROJECT.organization_id


def test_project_service_retrieves_correct_project_by_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_project = PROJECT
    project_service: ProjectService = ProjectService(repository_mock, FakeAuthContext())
    repository_mock.get_one_project.return_value = PROJECT

    actual_saved_project = project_service.get_one_project(PROJECT_ID, DUMMY_USER)

    assert actual_saved_project.id == expected_project.id
    assert actual_saved_project.name == expected_project.name


def test_project_service_retrieves__correct_project_by_organization_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_organization_id = ORGANIZATION_ID
    project_service: ProjectService = ProjectService(repository_mock, FakeAuthContext())
    repository_mock.get_projects_from_organization.return_value = [PROJECT]

    actual_projects = project_service.list_projects_from_organization(
        ORGANIZATION_ID, DUMMY_USER
    )

    assert actual_projects[0].organization_id == expected_organization_id
