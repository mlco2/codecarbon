from unittest import mock
from uuid import UUID

from carbonserver.api.infra.repositories.repository_projects_tokens import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import AccessLevel, ProjectToken, ProjectTokenCreate
from carbonserver.api.services.project_token_service import ProjectTokenService

PROJECT_ID = UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d")

PROJECT_TOKEN_ID = UUID("e60afb92-17b7-4720-91a0-1ae91e409ba7")

PROJECT_TOKEN = ProjectToken(
    id=PROJECT_TOKEN_ID,
    project_id=PROJECT_ID,
    name="Project",
    token="token",
    access=AccessLevel.READ.value,
)


@mock.patch("uuid.uuid4", return_value=PROJECT_TOKEN_ID)
def test_project_token_service_creates_correct_project_token(_):
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_id = PROJECT_TOKEN_ID
    project_token_service: ProjectTokenService = ProjectTokenService(repository_mock)
    repository_mock.add_project_token.return_value = PROJECT_TOKEN

    project_token_to_create = ProjectTokenCreate(
        name="Project",
        access=AccessLevel.READ.value,
    )

    actual_saved_project_token = project_token_service.add_project_token(
        str(PROJECT_ID), project_token_to_create
    )

    assert actual_saved_project_token.id == expected_id
    assert actual_saved_project_token.project_id == PROJECT_ID


def test_project_token_service_deletes_correct_project_token():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_token_service: ProjectTokenService = ProjectTokenService(repository_mock)
    repository_mock.delete_project_token.return_value = None

    project_token_service.delete_project_token(PROJECT_ID, PROJECT_TOKEN_ID)

    # Check that the repository delete_project method was called with the correct project_id
    repository_mock.delete_project_token.assert_called_once_with(
        PROJECT_ID, PROJECT_TOKEN_ID
    )


def test_project_token_service_retrieves_correct_tokens_by_project_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_project_token = PROJECT_TOKEN
    project_token_service: ProjectTokenService = ProjectTokenService(repository_mock)
    repository_mock.list_project_tokens.return_value = [PROJECT_TOKEN]

    response = project_token_service.list_tokens_from_project(PROJECT_ID)

    assert len(response) == 1
    assert response[0] == expected_project_token
