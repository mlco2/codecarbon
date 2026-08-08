from unittest import mock
from uuid import UUID

import pytest
from api.mocks import FakeAuthContext, FakeUserWithAuthDependency
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_pagination import add_pagination
from starlette import status

from carbonserver.api.routers import model_benchmarks
from carbonserver.api.schemas import ModelBenchmark
from carbonserver.api.services.auth_service import MandatoryUserWithAuthDependency
from carbonserver.api.services.model_benchmark_service import (
    BenchmarkValidationError,
    ModelBenchmarkService,
)
from carbonserver.container import ServerContainer

BENCHMARK_ID = "b1b9d5e0-58e8-45f0-9ef5-4549b3d6f3f0"

BENCHMARK = {
    "id": BENCHMARK_ID,
    "submitted_at": "2026-08-08T13:20:00",
    "submitted_by": None,
    "spec_version": "1.0.0-draft",
    "model_name": "mistralai/Mistral-7B-Instruct-v0.3",
    "model_revision": "e0bc86c",
    "quantization": "fp16",
    "engine": "vllm",
    "engine_version": "0.6.3",
    "deployment_id": "box-1",
    "deployment_label": "Paris box 1",
    "concurrency": 64,
    "input_token_bucket": 128,
    "gpu_model": "NVIDIA A100-SXM4-80GB",
    "gpu_count": 1,
    "infra_type": "onPremise",
    "duration": 143.7,
    "it_energy_kwh": 0.0166,
    "input_tokens": 84000,
    "output_tokens": 163840,
    "it_energy_per_token": 1.01e-07,
    "latency_per_token_s": 0.024,
    "record": {},
}


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[model_benchmarks])
    container.auth_context.override(FakeAuthContext())
    app = FastAPI()
    app.container = container
    app.include_router(model_benchmarks.router)
    app.dependency_overrides[MandatoryUserWithAuthDependency] = (
        lambda: FakeUserWithAuthDependency()
    )
    add_pagination(app)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def _service_mock(custom_test_server):
    service = mock.Mock(spec=ModelBenchmarkService)
    custom_test_server.container.model_benchmark_service.override(service)
    return service


def test_submit_benchmark(client, custom_test_server):
    service = _service_mock(custom_test_server)
    service.add_benchmark.return_value = UUID(BENCHMARK_ID)

    response = client.post("/model-benchmarks", json={"llmBenchmark": {}})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == BENCHMARK_ID


def test_invalid_submission_returns_every_failure(client, custom_test_server):
    """
    A submitter who has to re-run a 10-minute benchmark once per broken rule
    gives up. Report the whole list at once.
    """
    service = _service_mock(custom_test_server)
    service.add_benchmark.side_effect = BenchmarkValidationError(
        ["rule 2: measurementDuration 10s < 120s", "rule 5: forcedOutputLength"]
    )

    response = client.post("/model-benchmarks", json={"llmBenchmark": {}})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert len(response.json()["detail"]["failures"]) == 2


def test_read_benchmark(client, custom_test_server):
    service = _service_mock(custom_test_server)
    service.get_one_benchmark.return_value = ModelBenchmark(**BENCHMARK)

    response = client.get(f"/model-benchmarks/{BENCHMARK_ID}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["model_name"] == "mistralai/Mistral-7B-Instruct-v0.3"


def test_list_benchmarks(client, custom_test_server):
    service = _service_mock(custom_test_server)
    service.list_benchmarks.return_value = [ModelBenchmark(**BENCHMARK)]

    response = client.get("/model-benchmarks?model_name=mistralai/Mistral-7B")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["items"]) == 1


def test_export_snapshot_is_the_ecologits_surface(client, custom_test_server):
    """
    The snapshot carries the reference quantity plus enough context to judge
    whether it applies — not the raw record, and not the submitter.
    """
    from carbonserver.api.schemas import ModelBenchmarkReference

    service = _service_mock(custom_test_server)
    service.export_reference_snapshot.return_value = [
        ModelBenchmarkReference(
            id=UUID(BENCHMARK_ID),
            model_name="mistralai/Mistral-7B-Instruct-v0.3",
            quantization="fp16",
            engine="vllm",
            concurrency=64,
            gpu_model="NVIDIA A100-SXM4-80GB",
            gpu_count=1,
            it_energy_per_token=1.01e-07,
            latency_per_token_s=0.024,
            spec_version="1.0.0-draft",
        )
    ]

    response = client.get("/model-benchmarks/export")

    assert response.status_code == status.HTTP_200_OK
    entry = response.json()[0]
    assert entry["it_energy_per_token"] == 1.01e-07
    assert "record" not in entry
    assert "submitted_by" not in entry


def test_export_route_is_not_shadowed_by_the_id_route(client, custom_test_server):
    """`/export` must not be parsed as a benchmark id."""
    service = _service_mock(custom_test_server)
    service.export_reference_snapshot.return_value = []

    response = client.get("/model-benchmarks/export")

    assert response.status_code == status.HTTP_200_OK
    service.get_one_benchmark.assert_not_called()


def test_reads_need_no_authentication(custom_test_server):
    """Stored records are public; there is no review state to gate them on."""
    service = _service_mock(custom_test_server)
    service.get_one_benchmark.return_value = ModelBenchmark(**BENCHMARK)

    unauthenticated = TestClient(custom_test_server)
    response = unauthenticated.get(f"/model-benchmarks/{BENCHMARK_ID}")

    assert response.status_code == status.HTTP_200_OK


def test_list_filters_by_deployment(client, custom_test_server):
    service = _service_mock(custom_test_server)
    service.list_benchmarks.return_value = [ModelBenchmark(**BENCHMARK)]

    response = client.get("/model-benchmarks?deployment_id=box-1")

    assert response.status_code == status.HTTP_200_OK
    assert service.list_benchmarks.call_args.kwargs["deployment_id"] == "box-1"
