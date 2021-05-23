"""Tests module."""

from unittest import mock

import pytest
from container import ServerContainer
from fastapi.testclient import TestClient

from carbonserver.database.sql_models import User as ModelUser
from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from fastapi import status, FastAPI

from carbonserver.api.routers import users


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[users])
    app = FastAPI()
    app.container = container
    app.include_router(users.router)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_create_user(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_id = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
    expected_user = {
        "user_id": expected_id,
        "name": "Gontran Bonheur",
        "email": "xyz@email.com",
        "hashed_password": "pwd",
        "is_active": True,
    }
    repository_mock.create_user.return_value = ModelUser(**expected_user)

    user_to_create = {
        "name": "Gontran Bonheur",
        "email": "xyz@email.com",
        "password": "pwd",
    }

    container_mock = mock.Mock(spec=ServerContainer)
    container_mock.db.return_value = True
    with custom_test_server.container.user_repository.override(repository_mock):
        with custom_test_server.container.db.override(container_mock):
            response = client.post("/users/", json=user_to_create)
            actual_user = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert actual_user == expected_user
