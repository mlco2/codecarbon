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


@pytest.mark.skip()
def test_post_emission_not_implemented(emissions_router):
    app, client = emissions_router
    response = client.post("/emission")
    assert response.status_code == 405


@pytest.mark.skip()
def test_put_emission_returns_success_with_correct_object(emissions_router):
    app, client = emissions_router
    response = client.put(
        "/emission",
        json={
            "timestamp": "2021-04-04T08:43:00+02:00",
            "run_id": "40088f1a-d28e-4980-8d80-bf5600056a14",
            "duration": 98745,
            "emissions": 1.548444,
            "energy_consumed": 57.21874,
        },
    )
    assert response.status_code == 201


@pytest.mark.skip()
def test_put_emission_empty_returns_unprocessable(emissions_router):
    app, client = emissions_router
    response = client.put("/emission")
    assert response.status_code == 422


@pytest.mark.skip()
def test_read_emission_by_emission_id_returns_emission(emissions_router):
    app, client = emissions_router
    emission_id = "1"
    response = client.get("/emission/{emission_id}".format(emission_id=emission_id))

    assert response.status_code == 200
    assert response.json() == {
        "duration": 98745,
        "emissions": 1.548444,
        "energy_consumed": 57.21874,
        "id": 1,
        "run_id": "40088f1a-d28e-4980-8d80-bf5600056a14",
        "timestamp": "2021-04-04T08:43:00",
    }


@pytest.mark.skip()
def test_read_emission_by_emission_id_returns_not_found_error(emissions_router):
    app, client = emissions_router
    emission_id = "64565sd4f5g6sd4f65g4"
    response = client.get("/emission/{emission_id}".format(emission_id=emission_id))

    assert response.status_code == 404


@pytest.mark.skip()
def test_read_emissions_by_run_id_returns_not_found_error(emissions_router):
    app, client = emissions_router
    run_id = "1"
    response = client.get("/emissions/{run_id}".format(run_id=run_id))

    assert response.status_code == 404


@pytest.mark.skip()
def test_read_emission_returns_experiment_id_returns_not_found_error(emissions_router):
    app, client = emissions_router
    run_id = "wxcb46554vb4651"
    response = client.get("/emissions/{run_id}".format(run_id=run_id))

    assert response.status_code == 404
