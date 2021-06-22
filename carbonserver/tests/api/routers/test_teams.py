from unittest import mock

import pytest
from container import ServerContainer
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from carbonserver.api.infra.repositories.repository_teams import SqlAlchemyRepository
from carbonserver.api.routers import teams
from carbonserver.database.sql_models import Team as SqlModelTeam

ORG_ID = "f52fe339-164d-4c2b-a8c0-f562dfce0org"
ORG_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce0org"

TEAM_ID = "f52fe339-164d-4c2b-a8c0-f562dfceteam"
TEAM_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfceteam"

TEAM_TO_CREATE = {
    "name": "Data For Good Code Carbon",
    "description": "DFG Code Carbon Team",
    "organization_id": ORG_ID,
}

TEAM_1 = {
    "id": TEAM_ID,
    "name": "Data For Good Code Carbon",
    "description": "Data For Good Code Carbon Team",
    "organization_id": ORG_ID,
}


TEAM_2 = {
    "id": TEAM_ID_2,
    "name": "Data For Good Code Carbon 2",
    "description": "Data For Good Code Carbon Team 2",
    "organization_id": ORG_ID_2,
}


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[teams])
    app = FastAPI()
    app.container = container
    app.include_router(teams.router)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_add_team(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_team = TEAM_1
    repository_mock.add_team.return_value = SqlModelTeam(**TEAM_1)

    with custom_test_server.container.team_repository.override(repository_mock):
        response = client.put("/teams/", json=TEAM_TO_CREATE)
        actual_team = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert actual_team == expected_team


def test_get_team_by_id_returns_correct_team(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_team = TEAM_1
    repository_mock.get_one_team.return_value = [
        SqlModelTeam(**expected_team),
    ]

    with custom_test_server.container.team_repository.override(repository_mock):
        response = client.get("/teams/read_team/", params={"id": TEAM_ID})
        actual_team = response.json()[0]

    assert response.status_code == status.HTTP_200_OK
    assert actual_team == expected_team


def test_list_teams_returns_all_teams(client, custom_test_server):
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_team_1 = TEAM_1
    expected_team_2 = TEAM_2
    expected_team_list = [expected_team_1, expected_team_2]
    repository_mock.list_teams.return_value = [
        SqlModelTeam(**expected_team_1),
        SqlModelTeam(**expected_team_2),
    ]

    with custom_test_server.container.team_repository.override(repository_mock):
        response = client.get("/teams/")
        actual_team_list = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert actual_team_list == expected_team_list
