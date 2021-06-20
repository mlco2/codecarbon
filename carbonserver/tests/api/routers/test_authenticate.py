from unittest import mock

import pytest
from container import ServerContainer
from fastapi import FastAPI
from starlette import status
from starlette.testclient import TestClient

from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.api.routers import authenticate

USER_TO_VERIFY = {"email": "user8@example.com", "password": "password"}

USER_TO_VERIFY_BAD_PASSWORD = {"email": "user8@example.com", "password": "bad-password"}


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[authenticate])
    app = FastAPI()
    app.container = container
    app.include_router(authenticate.router)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_authenticate_should_return_an_access_token_is_password_is_valid(
    client, custom_test_server
):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    repository_mock.verify_user.return_value = True

    with custom_test_server.container.user_repository.override(repository_mock):
        response = client.post("/authenticate/", json=USER_TO_VERIFY)

    assert response.status_code == status.HTTP_200_OK


def test_authenticate_should_returns_an_error_if_password_is_invalid(
    client, custom_test_server
):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    repository_mock.verify_user.return_value = False

    with custom_test_server.container.user_repository.override(repository_mock):
        response = client.post("/authenticate/", json=USER_TO_VERIFY_BAD_PASSWORD)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
