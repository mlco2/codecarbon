from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import codecarbon.integrations.fastapi.middleware as cc_fastapi_middleware
from codecarbon.integrations.fastapi import add_codecarbon_middleware


@pytest.fixture
def app():
    application = FastAPI()

    @application.get("/items/{item_id}")
    def get_item(item_id: int):
        return {"item_id": item_id}

    @application.get("/health")
    def health():
        return {"ok": True}

    add_codecarbon_middleware(
        application,
        project_name="test-api",
        response_headers="emissions",
    )
    return application


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_tracks_routed_request(MockTracker, app):
    tracker_instance = MockTracker.return_value
    tracker_instance.stop.return_value = 0.001
    tracker_instance.final_emissions_data = MagicMock(
        emissions=0.001, duration=0.5, energy_consumed=0.002, emissions_rate=0.002
    )

    client = TestClient(app)
    response = client.get("/items/7")

    assert response.status_code == 200
    MockTracker.assert_called_once()
    tracker_instance.start.assert_called_once()
    tracker_instance.stop.assert_called_once()
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.001"


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_applies_default_response_headers(MockTracker):
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"ok": True}

    add_codecarbon_middleware(application, response_headers="default")
    tracker_instance = MockTracker.return_value
    tracker_instance.stop.return_value = 0.001
    tracker_instance.final_emissions_data = MagicMock(
        emissions=0.001,
        duration=1.2,
        energy_consumed=0.003,
        emissions_rate=0.0008,
    )

    response = TestClient(application).get("/predict")
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.001"
    assert response.headers["X-CodeCarbon-Duration-s"] == "1.2"
    assert response.headers["X-CodeCarbon-Energy-Consumed-kwh"] == "0.003"


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_custom_header_formatter(MockTracker):
    application = FastAPI()

    @application.get("/predict")
    def predict():
        return {"ok": True}

    def formatter(data, request):
        return {
            "X-CodeCarbon-Emissions-kg": f"{data.emissions:.4f}",
            "X-CodeCarbon-Route": request.url.path,
        }

    add_codecarbon_middleware(application, header_formatter=formatter)
    tracker_instance = MockTracker.return_value
    tracker_instance.stop.return_value = 0.001
    tracker_instance.final_emissions_data = MagicMock(emissions=0.001234)

    response = TestClient(application).get("/predict")
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.0012"
    assert response.headers["X-CodeCarbon-Route"] == "/predict"


@patch.object(cc_fastapi_middleware, "EmissionsTracker")
def test_middleware_skips_excluded_paths(MockTracker, app):
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    MockTracker.assert_not_called()
