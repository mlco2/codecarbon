import re
from unittest import mock

import pytest
from api.mocks import FakeAuthContext, FakeUserWithAuthDependency
from dependency_injector import providers
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.repositories.repository_projects_tokens import (
    SqlAlchemyRepository,
)
from carbonserver.api.routers import project_api_tokens
from carbonserver.api.schemas import ProjectToken
from carbonserver.api.services.auth_service import MandatoryUserWithAuthDependency
from carbonserver.container import ServerContainer

PROJECT_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"


PROJECT_TOKEN_ID = "c13e851f-5c2f-403d-98d0-51fe15df3bc3"

PROJECT_TOKEN_TO_CREATE = {
    "name": "Token API Code Carbon",
    "access": 2,
}

PROJECT_TOKEN = {
    "id": PROJECT_TOKEN_ID,
    "project_id": PROJECT_ID,
    "name": "Token API Code Carbon",
    "token": "cpt_some_token",
    "access": 2,
    "last_used": None,
    "revoked": False,
}


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[project_api_tokens])
    app = FastAPI()
    app.container = container
    app.include_router(project_api_tokens.router)
    app.dependency_overrides[MandatoryUserWithAuthDependency] = (
        FakeUserWithAuthDependency
    )
    app.container.auth_context.override(providers.Factory(FakeAuthContext))
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_add_project_token(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_project_token = PROJECT_TOKEN
    repository_mock.add_project_token.return_value = ProjectToken(**PROJECT_TOKEN)

    with custom_test_server.container.project_token_repository.override(
        repository_mock
    ):
        response = client.post(
            "/projects/{PROJECT_ID}/api-tokens", json=PROJECT_TOKEN_TO_CREATE
        )
        actual_project_token = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    # Check all fields except 'token'
    for key in expected_project_token:
        if key != "token":
            assert actual_project_token[key] == expected_project_token[key]

    # Check token format: cpt_ + 32 alphanumeric chars
    assert re.fullmatch(r"cpt_[a-zA-Z0-9_\-]{43,44}", actual_project_token["token"])


def test_delete_project_token(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    repository_mock.delete_project_token.return_value = None

    with custom_test_server.container.project_token_repository.override(
        repository_mock
    ):
        response = client.delete(
            f"/projects/{PROJECT_ID}/api-tokens/{PROJECT_TOKEN_ID}"
        )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    repository_mock.delete_project_token.assert_called_once_with(
        PROJECT_ID, PROJECT_TOKEN_ID
    )


def test_get_projects_from_organization_returns_correct_project(
    client, custom_test_server
):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_project_token = PROJECT_TOKEN
    expected_project_token_list = [expected_project_token]
    repository_mock.list_project_tokens.return_value = [
        ProjectToken(**expected_project_token),
    ]

    with custom_test_server.container.project_token_repository.override(
        repository_mock
    ):
        response = client.get(f"/projects/{PROJECT_ID}/api-tokens")
        actual_project_token_list = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_project_token_list == expected_project_token_list
