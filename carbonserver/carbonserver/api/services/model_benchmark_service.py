"""
Ingestion and curation of LLM energy benchmarks.

Submitted records are BoAmps reports conforming to the profile in
``specs/llm-energy-benchmark-v1.md``. This service applies the §6 validity
rules, extracts the queryable columns, and computes the derived quantities of
§5.4. A record that passes the rules is stored and is immediately readable:
there is no review step.

The validity rules are imported from ``codecarbon.benchmark.validation`` rather
than reimplemented. They are the ingestion gate, and two copies of a gate drift
apart; the harness runs the same code locally so a submitter finds a problem on
the machine that produced it.
"""

import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from codecarbon.benchmark.validation import validate_record

from carbonserver.api.infra.repositories.repository_model_benchmarks import (
    SqlAlchemyRepository as ModelBenchmarkSqlRepository,
)
from carbonserver.api.schemas import (
    ModelBenchmark,
    ModelBenchmarkBase,
    ModelBenchmarkReference,
    User,
)


class BenchmarkValidationError(Exception):
    """A submission failed the §6 rules. Carries every failure, not just the first."""

    def __init__(self, failures: List[str]):
        self.failures = failures
        super().__init__("; ".join(failures))


def _dataset_quantity(record: Dict[str, Any], usage: str) -> Optional[int]:
    for entry in (record.get("task") or {}).get("dataset") or []:
        if entry.get("dataUsage") == usage:
            quantity = entry.get("dataQuantity")
            return int(quantity) if quantity is not None else None
    return None


def _normalise_component_name(name: Optional[str]) -> Optional[str]:
    """
    Strip the leading count CodeCarbon bakes into a component name.

    CodeCarbon reports GPUs as "1 x NVIDIA A100-SXM4-80GB" (the BoAmps hardware
    schema cites that exact shape), but the count already has its own field in
    ``nbComponent``. Keeping it in the name would double-report it and, worse,
    make the ``gpu_model`` filter unusable: nobody searches for "1 x NVIDIA
    A100-SXM4-80GB".
    """
    if not name:
        return name
    return re.sub(r"^\s*\d+\s*x\s*", "", name).strip() or None


def _component(record: Dict[str, Any], component_type: str) -> Dict[str, Any]:
    for component in (record.get("infrastructure") or {}).get("components") or []:
        if component.get("componentType") == component_type:
            return component
    return {}


def extract_fields(record: Dict[str, Any]) -> ModelBenchmarkBase:
    """
    Pull the queryable columns out of a BoAmps record.

    ``it_energy_per_token`` and ``latency_per_token_s`` are computed here and
    never read from the submission (spec §5.4). Accepting them would make the
    stored normalization unreproducible: when the spec changes how per-token
    energy is defined, the whole corpus has to be recomputable from raw values.
    """
    extension = record.get("llmBenchmark") or {}
    measure = (record.get("measures") or [{}])[0]
    algorithm = ((record.get("task") or {}).get("algorithms") or [{}])[0]
    gpu = _component(record, "gpu")

    energy = float(measure.get("powerConsumption") or 0)
    output_tokens = _dataset_quantity(record, "output") or 0
    tps = extension.get("tpsPerRequestP50")

    return ModelBenchmarkBase(
        spec_version=extension.get("specVersion"),
        model_name=algorithm.get("foundationModelName"),
        model_revision=extension.get("modelRevision"),
        quantization=algorithm.get("quantization"),
        engine=algorithm.get("framework"),
        engine_version=algorithm.get("frameworkVersion"),
        deployment_id=extension.get("deploymentId"),
        deployment_label=extension.get("deploymentLabel"),
        concurrency=int(extension.get("concurrency") or 0),
        input_token_bucket=extension.get("inputTokenBucket"),
        gpu_model=_normalise_component_name(gpu.get("componentName")),
        gpu_count=gpu.get("nbComponent"),
        infra_type=(record.get("infrastructure") or {}).get("infraType"),
        duration=float(measure.get("measurementDuration") or 0),
        it_energy_kwh=energy,
        input_tokens=_dataset_quantity(record, "input"),
        output_tokens=output_tokens,
        it_energy_per_token=energy / output_tokens if output_tokens else 0.0,
        latency_per_token_s=1.0 / float(tps) if tps else None,
    )


class ModelBenchmarkService:
    def __init__(self, model_benchmark_repository: ModelBenchmarkSqlRepository):
        self._repository = model_benchmark_repository

    def add_benchmark(self, record: Dict[str, Any], user: Optional[User]) -> UUID:
        """Validate and store a submission."""
        failures = validate_record(record)
        if failures:
            raise BenchmarkValidationError(failures)
        extracted = extract_fields(record)
        return self._repository.add_benchmark(
            record=record,
            extracted=extracted,
            submitted_by=user.id if user else None,
        )

    def get_one_benchmark(self, benchmark_id: UUID) -> ModelBenchmark:
        return self._repository.get_one_benchmark(benchmark_id)

    def list_benchmarks(
        self,
        model_name: Optional[str] = None,
        concurrency: Optional[int] = None,
        gpu_model: Optional[str] = None,
        deployment_id: Optional[str] = None,
    ) -> List[ModelBenchmark]:
        return self._repository.list_benchmarks(
            model_name=model_name,
            concurrency=concurrency,
            gpu_model=gpu_model,
            deployment_id=deployment_id,
        )

    def export_reference_snapshot(
        self, model_name: Optional[str] = None, deployment_id: Optional[str] = None
    ) -> List[ModelBenchmarkReference]:
        """
        The reference snapshot a consumer such as EcoLogits reads.

        Fetched once and cached rather than queried per LLM call: a per-request
        lookup would couple the caller's availability to this service and add
        network latency inside a library that wraps
        ``client.chat.completions.create``.
        """
        stored = self._repository.list_benchmarks(
            model_name=model_name,
            deployment_id=deployment_id,
        )
        return [
            ModelBenchmarkReference(
                id=b.id,
                model_name=b.model_name,
                model_revision=b.model_revision,
                quantization=b.quantization,
                engine=b.engine,
                engine_version=b.engine_version,
                deployment_id=b.deployment_id,
                deployment_label=b.deployment_label,
                concurrency=b.concurrency,
                gpu_model=b.gpu_model,
                gpu_count=b.gpu_count,
                it_energy_per_token=b.it_energy_per_token,
                latency_per_token_s=b.latency_per_token_s,
                spec_version=b.spec_version,
            )
            for b in stored
        ]
