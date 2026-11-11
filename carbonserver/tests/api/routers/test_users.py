from unittest import mock

import pytest
from api.mocks import USER_ID_1, FakeUserWithAuthDependency
from dependency_injector import providers
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.api.routers import users
from carbonserver.api.routers.authenticate import (
    ID_TOKEN_COOKIE_NAME,
    SESSION_COOKIE_NAME,
)
from carbonserver.api.services.auth_service import MandatoryUserWithAuthDependency
from carbonserver.container import ServerContainer


class FakeUserMissingFromDb:
    auth_user = {"sub": USER_ID_1}
    db_user = None


@pytest.fixture
def auth_provider_mock():
    provider = mock.Mock()
    provider.revoke_token = mock.AsyncMock()
    return provider


@pytest.fixture
def custom_test_server(auth_provider_mock):
    container = ServerContainer()
    container.wire(modules=[users])
    app = FastAPI()
    app.container = container
    app.include_router(users.router)
    app.dependency_overrides[MandatoryUserWithAuthDependency] = (
        FakeUserWithAuthDependency
    )
    container.auth_provider.override(providers.Object(auth_provider_mock))
    yield app
    container.auth_provider.reset_override()


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


@pytest.fixture
def repository_mock(custom_test_server):
    repository = mock.Mock(spec=SqlAlchemyRepository)
    repository.delete_user.return_value = []
    with custom_test_server.container.user_repository.override(repository):
        yield repository


def test_delete_current_user_erases_them_and_signs_them_out(
    client, repository_mock, auth_provider_mock
):
    client.cookies.set(SESSION_COOKIE_NAME, "access-token")
    client.cookies.set(ID_TOKEN_COOKIE_NAME, "id-token")

    response = client.delete("/users/me")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    repository_mock.delete_user.assert_called_once_with(
        FakeUserWithAuthDependency.db_user.id
    )
    auth_provider_mock.revoke_token.assert_awaited_once_with("access-token")
    cleared = response.headers.get_list("set-cookie")
    assert any(c.startswith(f"{SESSION_COOKIE_NAME}=") for c in cleared)
    assert any(c.startswith(f"{ID_TOKEN_COOKIE_NAME}=") for c in cleared)


def test_delete_current_user_with_bearer_token_skips_revocation(
    client, repository_mock, auth_provider_mock
):
    response = client.delete("/users/me")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    repository_mock.delete_user.assert_called_once()
    auth_provider_mock.revoke_token.assert_not_awaited()


def test_delete_current_user_is_idempotent(client, custom_test_server, repository_mock):
    custom_test_server.dependency_overrides[MandatoryUserWithAuthDependency] = (
        FakeUserMissingFromDb
    )

    response = client.delete("/users/me")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    repository_mock.delete_user.assert_not_called()


def test_delete_current_user_requires_authentication(repository_mock):
    container = ServerContainer()
    container.wire(modules=[users])
    app = FastAPI()
    app.container = container
    app.include_router(users.router)

    with container.user_repository.override(repository_mock):
        response = TestClient(app).delete("/users/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    repository_mock.delete_user.assert_not_called()
