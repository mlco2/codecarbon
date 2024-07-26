from unittest import mock
from uuid import UUID

import pytest
from fastapi import HTTPException

from carbonserver.api.infra.repositories.repository_projects_tokens import (
    SqlAlchemyRepository,
)
from carbonserver.api.schemas import AccessLevel, ProjectToken, ProjectTokenCreate
from carbonserver.api.services.project_token_service import ProjectTokenService

PROJECT_ID = UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d")
EXPERIMENT_ID = UUID("f22fe339-164d-4c2b-a8c0-f562dfce066e")
RUN_ID = UUID("f11fe339-164d-4c2b-a8c0-f562dfce066e")
EMISSION_ID = UUID("f42fe339-164d-4c2b-a8c0-f562dfce065e")

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


# Access tests


def test_project_token_service_has_access_to_project_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_token_service: ProjectTokenService = ProjectTokenService(repository_mock)
    repository_mock.get_project_token_by_project_id_and_token.return_value = (
        PROJECT_TOKEN
    )

    response_read = project_token_service.project_token_has_access_to_project_id(
        AccessLevel.READ.value, PROJECT_ID, "token"
    )

    assert response_read is None
    # Check that the repository get_project_token_by_project_id_and_token method was called with the correct project_id

    repository_mock.get_project_token_by_project_id_and_token.assert_called_once_with(
        PROJECT_ID, "token"
    )


def test_project_token_service_has_access_to_project_id_write():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_token_service: ProjectTokenService = ProjectTokenService(repository_mock)
    repository_mock.get_project_token_by_project_id_and_token.return_value = (
        PROJECT_TOKEN
    )

    with pytest.raises(HTTPException) as exc:
        project_token_service.project_token_has_access_to_project_id(
            AccessLevel.WRITE.value, PROJECT_ID, "token"
        )
    assert exc.value.status_code == 403
    assert exc.value.detail == "Not allowed to perform this action"

    # Check that the repository get_project_token_by_project_id_and_token method was called with the correct project_id
    repository_mock.get_project_token_by_project_id_and_token.assert_called_once_with(
        PROJECT_ID, "token"
    )


def test_project_token_service_has_access_to_experiment_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_token_service: ProjectTokenService = ProjectTokenService(repository_mock)
    repository_mock.get_project_token_by_experiment_id_and_token.return_value = (
        PROJECT_TOKEN
    )

    response_read = project_token_service.project_token_has_access_to_experiment_id(
        AccessLevel.READ.value, EXPERIMENT_ID, "token"
    )

    assert response_read is None
    # Check that the repository get_project_token_by_experiment_id_and_token method was called with the correct project_id

    repository_mock.get_project_token_by_experiment_id_and_token.assert_called_once_with(
        EXPERIMENT_ID, "token"
    )


def test_project_token_service_has_access_to_run_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_token_service: ProjectTokenService = ProjectTokenService(repository_mock)
    repository_mock.get_project_token_by_run_id_and_token.return_value = PROJECT_TOKEN

    response_read = project_token_service.project_token_has_access_to_run_id(
        AccessLevel.READ.value, RUN_ID, "token"
    )

    assert response_read is None
    # Check that the repository get_project_token_by_experiment_id_and_token method was called with the correct project_id

    repository_mock.get_project_token_by_run_id_and_token.assert_called_once_with(
        RUN_ID, "token"
    )


def test_project_token_service_has_access_to_emission_id():
    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    project_token_service: ProjectTokenService = ProjectTokenService(repository_mock)
    repository_mock.get_project_token_by_emission_id_and_token.return_value = (
        PROJECT_TOKEN
    )

    response_read = project_token_service.project_token_has_access_to_emission_id(
        AccessLevel.READ.value, EMISSION_ID, "token"
    )

    assert response_read is None
    # Check that the repository get_project_token_by_experiment_id_and_token method was called with the correct project_id

    repository_mock.get_project_token_by_emission_id_and_token.assert_called_once_with(
        EMISSION_ID, "token"
    )
