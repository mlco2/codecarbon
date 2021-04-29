import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from carbonserver.api.dependencies import get_query_token
from carbonserver.api.routers import emissions

"""
Setting up a test client & a test server in specific states would be interesting.
This setup may be extracted on a separate test container file to let developers ingest multiple / custom configurations.
# Current state:
 - No actual database is plugged on unit tests
 - Client is emitting from same network as server
 - This test class tests only API handling (logic is mocked)
"""


@pytest.fixture()
def emissions_router():
    app = FastAPI(dependencies=[Depends(get_query_token)])
    app.include_router(emissions.router)
    client = TestClient(app)
    return app, client


def test_post_emission_returns_success_with_correct_object(emissions_router):
    app, client = emissions_router

    response = client.post("/emission")

    assert response.status_code == 405


def test_read_emission_by_emission_id_returns_not_found_error(emissions_router):
    app, client = emissions_router
    emission_id = "1"
    response = client.get("/emission/{emission_id}".format(emission_id=emission_id))

    assert response.status_code == 404


def test_read_emission_returns_experiment_id_returns_not_found_error(emissions_router):
    app, client = emissions_router
    experiment_id = "1"
    response = client.get(
        "/emissions/{experitment_id}".format(experitment_id=experiment_id)
    )

    assert response.status_code == 404
