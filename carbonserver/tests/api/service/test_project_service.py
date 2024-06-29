from unittest import mock
from uuid import UUID

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
    project_service: ProjectService = ProjectService(repository_mock)
    repository_mock.add_project.return_value = PROJECT

    project_to_create = ProjectCreate(
        name="Project",
        description="Description",
        organization_id=ORGANIZATION_ID,
    )

    actual_saved_project_id = project_service.add_project(project_to_create)

    assert actual_saved_project_id.id == expected_id


def test_project_service_deletes_correct_project():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_service: ProjectService = ProjectService(repository_mock)
    repository_mock.delete_project.return_value = None

    project_service.delete_project(PROJECT_ID)

    # Check that the repository delete_project method was called with the correct project_id
    repository_mock.delete_project.assert_called_once_with(PROJECT_ID)


def test_project_service_patches_correct_project():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_service: ProjectService = ProjectService(repository_mock)
    repository_mock.patch_project.return_value = PROJECT

    actual_saved_project = project_service.patch_project(PROJECT_ID, PROJECT)

    assert actual_saved_project.id == PROJECT.id
    assert actual_saved_project.name == PROJECT.name
    assert actual_saved_project.description == PROJECT.description
    assert actual_saved_project.organization_id == PROJECT.organization_id


def test_project_service_retrieves_correct_project_by_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_project = PROJECT
    project_service: ProjectService = ProjectService(repository_mock)
    repository_mock.get_one_project.return_value = PROJECT

    actual_saved_project = project_service.get_one_project(PROJECT_ID)

    assert actual_saved_project.id == expected_project.id
    assert actual_saved_project.name == expected_project.name


def test_project_service_retrieves__correct_project_by_organization_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_organization_id = ORGANIZATION_ID
    project_service: ProjectService = ProjectService(repository_mock)
    repository_mock.get_projects_from_organization.return_value = [PROJECT]

    actual_projects = project_service.list_projects_from_organization(ORGANIZATION_ID)

    assert actual_projects[0].organization_id == expected_organization_id
