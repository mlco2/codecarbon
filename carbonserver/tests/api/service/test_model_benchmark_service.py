from unittest import mock
from uuid import UUID

import pytest
from api.mocks import DUMMY_USER

from carbonserver.api.infra.repositories.repository_model_benchmarks import (
    SqlAlchemyRepository as ModelBenchmarkRepository,
)
from carbonserver.api.schemas import ModelBenchmark
from carbonserver.api.services.model_benchmark_service import (
    BenchmarkValidationError,
    ModelBenchmarkService,
    extract_fields,
)

BENCHMARK_ID = "b1b9d5e0-58e8-45f0-9ef5-4549b3d6f3f0"


def valid_record():
    """A record that satisfies every §6 rule."""
    energy = {"cpu": 0.004, "gpu": 0.012, "ram": 0.0006}
    return {
        "header": {
            "licensing": "Creative Commons 4.0",
            "reportDatetime": "2026-08-08 13:20:00",
            "publisher": {"name": "DFG", "confidentialityLevel": "public"},
        },
        "task": {
            "taskStage": "inference",
            "taskFamily": "chatbot",
            "nbRequest": 640,
            "algorithms": [
                {
                    "algorithmType": "llm",
                    "foundationModelName": "mistralai/Mistral-7B-Instruct-v0.3",
                    "parametersNumber": 7.25,
                    "quantization": "fp16",
                    "framework": "vllm",
                    "frameworkVersion": "0.6.3",
                }
            ],
            "dataset": [
                {"dataUsage": "input", "dataType": "token", "dataQuantity": 84000},
                {"dataUsage": "output", "dataType": "token", "dataQuantity": 163840},
            ],
        },
        "measures": [
            {
                "measurementMethod": "codecarbon",
                "version": "3.0.6",
                "cpuTrackingMode": "intel_rapl",
                "gpuTrackingMode": "nvml",
                "averageUtilizationGpu": 0.92,
                "powerConsumption": sum(energy.values()),
                "measurementDuration": 143.7,
                "powerCalibrationMeasurement": 0.00076,
                "durationCalibrationMeasurement": 30.0,
            }
        ],
        "system": {"os": "Linux"},
        "software": {"language": "python", "version": "3.11.0"},
        "infrastructure": {
            "infraType": "onPremise",
            "components": [
                {"componentType": "cpu", "nbComponent": 1, "share": 1},
                {
                    "componentType": "gpu",
                    "componentName": "NVIDIA A100-SXM4-80GB",
                    "nbComponent": 1,
                    "share": 1,
                },
                {"componentType": "ram", "nbComponent": 1, "share": 1},
            ],
        },
        "environment": {"country": "France"},
        "llmBenchmark": {
            "specVersion": "1.0.0-draft",
            "concurrency": 64,
            "inputTokenBucket": 128,
            "forcedOutputLength": True,
            "warmupRequests": 8,
            "nWindows": 3,
            "relativeSpread": 0.041,
            "tpsPerRequestP50": 41.6,
            "modelRevision": "e0bc86c",
            "energyBreakdownKwh": energy,
        },
    }


def service():
    repository = mock.Mock(spec=ModelBenchmarkRepository)
    return ModelBenchmarkService(repository), repository


def stored(submitted_by=None):
    return ModelBenchmark(
        id=UUID(BENCHMARK_ID),
        submitted_at="2026-08-08T13:20:00",
        submitted_by=submitted_by,
        spec_version="1.0.0-draft",
        model_name="mistralai/Mistral-7B-Instruct-v0.3",
        quantization="fp16",
        engine="vllm",
        concurrency=64,
        duration=143.7,
        it_energy_kwh=0.0166,
        output_tokens=163840,
        it_energy_per_token=1.01e-07,
        record={},
    )


class TestExtraction:
    def test_pulls_query_columns_from_the_record(self):
        fields = extract_fields(valid_record())
        assert fields.model_name == "mistralai/Mistral-7B-Instruct-v0.3"
        assert fields.concurrency == 64
        assert fields.gpu_model == "NVIDIA A100-SXM4-80GB"
        assert fields.engine_version == "0.6.3"
        assert fields.infra_type == "onPremise"

    def test_derived_fields_are_computed_not_read(self):
        """
        §5.4: the server recomputes per-token energy so the corpus stays
        recomputable when the normalization changes.
        """
        record = valid_record()
        record["llmBenchmark"]["itEnergyPerToken"] = 999.0  # must be ignored
        fields = extract_fields(record)
        assert fields.it_energy_per_token == pytest.approx(0.0166 / 163840)
        assert fields.latency_per_token_s == pytest.approx(1 / 41.6)

    def test_gpu_model_drops_the_count_prefix(self):
        """
        CodeCarbon names GPUs "1 x NVIDIA A100-SXM4-80GB". Keeping the count in
        the name double-reports it and makes the gpu_model filter unusable.
        """
        record = valid_record()
        record["infrastructure"]["components"][1][
            "componentName"
        ] = "2 x NVIDIA A100-SXM4-80GB"
        fields = extract_fields(record)
        assert fields.gpu_model == "NVIDIA A100-SXM4-80GB"

    def test_plain_gpu_name_is_left_alone(self):
        assert extract_fields(valid_record()).gpu_model == "NVIDIA A100-SXM4-80GB"

    def test_missing_tps_leaves_latency_null(self):
        record = valid_record()
        del record["llmBenchmark"]["tpsPerRequestP50"]
        assert extract_fields(record).latency_per_token_s is None


class TestIngestion:
    def test_valid_record_is_stored(self):
        svc, repository = service()
        repository.add_benchmark.return_value = UUID(BENCHMARK_ID)
        assert svc.add_benchmark(valid_record(), user=DUMMY_USER) == UUID(BENCHMARK_ID)

    def test_invalid_record_is_rejected_with_every_failure(self):
        svc, repository = service()
        record = valid_record()
        record["llmBenchmark"]["forcedOutputLength"] = False
        record["llmBenchmark"]["nWindows"] = 1
        with pytest.raises(BenchmarkValidationError) as exc:
            svc.add_benchmark(record, user=DUMMY_USER)
        assert len(exc.value.failures) >= 2
        repository.add_benchmark.assert_not_called()

    def test_submission_records_its_submitter(self):
        """No review state, but a stored record still says who supplied it."""
        svc, repository = service()
        svc.add_benchmark(valid_record(), user=DUMMY_USER)
        assert (
            repository.add_benchmark.call_args.kwargs["submitted_by"] == DUMMY_USER.id
        )


class TestReads:
    def test_stored_records_are_readable(self):
        svc, repository = service()
        repository.get_one_benchmark.return_value = stored()
        assert svc.get_one_benchmark(UUID(BENCHMARK_ID)) is not None

    def test_listing_applies_the_query_filters(self):
        svc, repository = service()
        repository.list_benchmarks.return_value = []
        svc.list_benchmarks(model_name="m", concurrency=64, deployment_id="box-1")
        kwargs = repository.list_benchmarks.call_args.kwargs
        assert kwargs["model_name"] == "m"
        assert kwargs["concurrency"] == 64
        assert kwargs["deployment_id"] == "box-1"

    def test_snapshot_exports_every_stored_record(self):
        svc, repository = service()
        repository.list_benchmarks.return_value = [stored()]
        snapshot = svc.export_reference_snapshot()
        assert snapshot[0].it_energy_per_token == 1.01e-07
        # The snapshot is narrow on purpose: no raw record, no submitter.
        assert not hasattr(snapshot[0], "record")

    def test_snapshot_can_be_scoped_to_a_deployment(self):
        svc, repository = service()
        repository.list_benchmarks.return_value = []
        svc.export_reference_snapshot(deployment_id="box-2")
        assert repository.list_benchmarks.call_args.kwargs["deployment_id"] == "box-2"
