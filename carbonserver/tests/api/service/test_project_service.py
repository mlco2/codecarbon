from unittest import mock
from uuid import UUID

from carbonserver.api.infra.repositories.repository_projects import SqlAlchemyRepository
from carbonserver.api.schemas import Project, ProjectCreate
from carbonserver.api.services.project_service import ProjectService

PROJECT_ID = UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d")

TEAM_ID = UUID("e52fe339-164d-4c2b-a8c0-f562dfce066d")

PROJECT = Project(
    id=PROJECT_ID, name="Project", description="Description", team_id=TEAM_ID
)


@mock.patch("uuid.uuid4", return_value=PROJECT_ID)
def test_project_service_creates_correct_project(_):
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_id = PROJECT_ID
    project_service: ProjectService = ProjectService(repository_mock)
    repository_mock.add_project.return_value = PROJECT

    project_to_create = ProjectCreate(
        name="Project", description="Description", team_id=TEAM_ID
    )

    actual_saved_project_id = project_service.add_project(project_to_create)

    assert actual_saved_project_id.id == expected_id


def test_project_service_retrieves_correct_project_by_id():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_project = PROJECT
    organization_service: ProjectService = ProjectService(repository_mock)
    repository_mock.get_one_project.return_value = PROJECT

    actual_saved_project = organization_service.get_one_project(PROJECT_ID)

    assert actual_saved_project.id == expected_project.id
    assert actual_saved_project.name == expected_project.name


def test_project_service_retrieves__correct_project_by_team_id():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_team_id = TEAM_ID
    project_service: ProjectService = ProjectService(repository_mock)
    repository_mock.get_projects_from_team.return_value = [PROJECT]

    actual_projects = project_service.list_projects_from_team(TEAM_ID)

    assert actual_projects[0].team_id == expected_team_id
