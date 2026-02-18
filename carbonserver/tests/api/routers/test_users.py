from unittest import mock

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.repositories.repository_users import (
    SqlAlchemyRepository as UsersRepository,
)
from carbonserver.api.routers import users
from carbonserver.api.schemas import User
from carbonserver.container import ServerContainer

USER_ID_1 = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
USER_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"

USER_1 = {
    "id": USER_ID_1,
    "name": "Gontran Bonheur",
    "email": "xyz@email.com",
    "organizations": [],
    "is_active": True,
}

USER_2 = {
    "id": USER_ID_2,
    "name": "Jonnhy Monnay",
    "email": "1234+1@email.fr",
    "organizations": [],
    "is_active": True,
}

###
#  Only needed for the steps after the creation of a user
###
PROJECT_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
ORGANIZATION_ID = "c13e851f-5c2f-403d-98d0-51fe15df3bc3"

PROJECT_1 = {
    "id": PROJECT_ID,
    "name": "Gontran Bonheur",
    "description": "Default project",
    "organization_id": ORGANIZATION_ID,
    "experiments": [],
}

ORG_1 = {
    "id": ORGANIZATION_ID,
    "name": "Gontran Bonheur",
    "description": "Default organization",
}


###


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


def test_get_user_by_id_returns_correct_user_with_correct_id(
    client, custom_test_server
):
    repository_mock = mock.Mock(spec=UsersRepository)
    expected_user = USER_1
    repository_mock.get_user_by_id.return_value = User(**expected_user)

    container_mock = mock.Mock(spec=ServerContainer)
    container_mock.db.return_value = True
    with custom_test_server.container.user_repository.override(repository_mock):
        response = client.get("/users/get_user_by_id/", params={"user_id": USER_ID_1})
        actual_user = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_user == expected_user
