"""
BoAmps record assembly for the LLM energy benchmark.

A benchmark record is a valid BoAmps 1.1.0 report satisfying the profile
constraints in spec §5.2, carrying the ``llmBenchmark`` extension of §5.3.

The BoAmps report is built by CodeCarbon's existing exporter
(``codecarbon.output_methods.boamps``) and then corrected where the exporter's
generic behaviour is not accurate enough for a reference measurement — see
``_fix_measure`` and ``_fix_components``.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from codecarbon.benchmark.runner import BenchmarkResult
from codecarbon.benchmark.validation import SPEC_VERSION
from codecarbon.core.util import count_physical_cpus
from codecarbon.output_methods.boamps import (
    BoAmpsAlgorithm,
    BoAmpsDataset,
    BoAmpsHeader,
    BoAmpsPublisher,
    BoAmpsTask,
    map_emissions_to_boamps,
)

# Float and integer formats, plus GGUF's own quantization type names used
# verbatim in lowercase. GGUF names are a controlled vocabulary defined by
# llama.cpp, so accepting them keeps records comparable without inventing a
# mapping -- and a 1-bit model like Bonsai's Q1_0 has no honest equivalent
# among fp16/int8/int4.
QUANTIZATIONS = (
    "fp32",
    "fp16",
    "bf16",
    "int8",
    "int4",
    "q1_0",
    "q2_0",
    "q2_k",
    "q3_k_m",
    "q4_0",
    "q4_k_m",
    "q5_k_m",
    "q6_k",
    "q8_0",
    "tq1_0",
    "tq2_0",
)


@dataclass
class ModelMetadata:
    """Model identity the harness cannot detect and the submitter must supply."""

    name: str
    parameters_number: float  # billions, total
    quantization: str
    uri: Optional[str] = None
    revision: Optional[str] = None
    active_parameters_number: Optional[float] = None
    tensor_parallel_size: Optional[int] = None

    def __post_init__(self):
        if self.quantization not in QUANTIZATIONS:
            raise ValueError(
                f"quantization must be one of {', '.join(QUANTIZATIONS)}, "
                f"got '{self.quantization}'. The vocabulary is pinned by the "
                "profile (spec §5.2) because BoAmps leaves it free text."
            )
        if self.active_parameters_number is None:
            self.active_parameters_number = self.parameters_number


def build_boamps_record(
    result: BenchmarkResult,
    model: ModelMetadata,
    publisher_name: str,
    licensing: str = "Creative Commons 4.0",
    facility_pue: Optional[float] = None,
    task_family: str = "chatbot",
    infra_type: Optional[str] = None,
    deployment_id: Optional[str] = None,
    deployment_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble the BoAmps record for a completed benchmark."""
    window = result.median_window

    task = BoAmpsTask(
        task_stage="inference",
        task_family=task_family,
        nb_request=window.n_requests,
        algorithms=[
            BoAmpsAlgorithm(
                algorithm_type="llm",
                foundation_model_name=model.name,
                foundation_model_uri=model.uri,
                parameters_number=model.parameters_number,
                quantization=model.quantization,
                framework=result.backend_info.name,
                framework_version=result.backend_info.version,
            )
        ],
        dataset=[
            BoAmpsDataset(
                data_usage="input",
                data_type="token",
                data_quantity=window.input_tokens,
            ),
            BoAmpsDataset(
                data_usage="output",
                data_type="token",
                data_quantity=window.output_tokens,
            ),
        ],
        task_description=(
            f"LLM energy benchmark, spec {SPEC_VERSION}, "
            f"concurrency {result.config.concurrency}, "
            f"input bucket {result.config.input_bucket} tokens, "
            f"{result.config.output_tokens} output tokens per request."
        ),
    )

    header = BoAmpsHeader(
        licensing=licensing,
        report_status="draft",
        publisher=BoAmpsPublisher(
            name=publisher_name,
            confidentiality_level="public",
        ),
    )

    report = map_emissions_to_boamps(
        emissions=window.emissions_data,
        task=task,
        header=header,
        quality="high",
    )

    _fix_measure(report, result)
    _fix_components(report, infra_type)

    record = report.to_dict()
    record["llmBenchmark"] = _extension(
        result, model, facility_pue, deployment_id, deployment_label
    )
    return record


def _fix_measure(report, result: BenchmarkResult) -> None:
    """
    Correct the auto-generated measure block.

    Three changes:

    * ``powerConsumption`` is set from the explicit CPU+GPU+RAM sum rather than
      ``energy_consumed``. They are equal only because the harness pins PUE to
      1.0 (spec §3.1); computing the sum makes that independent of tracker
      configuration instead of relying on it.
    * ``cpuTrackingMode`` / ``gpuTrackingMode`` are filled in, which the
      exporter cannot do (``mapper.py:116-119``).
    * The calibration measurement of §3.4 is attached.
    """
    window = result.median_window
    measure = report.measures[0]
    measure.power_consumption = window.energy_kwh
    measure.measurement_duration = window.duration_s
    measure.cpu_tracking_mode = result.cpu_tracking_mode
    measure.gpu_tracking_mode = result.gpu_tracking_mode
    measure.power_calibration_measurement = result.calibration_kwh
    measure.duration_calibration_measurement = result.calibration_duration_s


def _fix_components(report, infra_type: Optional[str]) -> None:
    """
    Correct the auto-generated hardware components.

    * ``share`` is set explicitly to 1. The profile requires it (spec §5.2) and
      the exporter never emits it; an absent share is indistinguishable from a
      shared GPU, which validity rule 9 rejects.
    * CPU ``nbComponent`` is replaced with the physical socket count. The
      exporter derives it as ``cpu_count // 2`` (``mapper.py:166``), which
      hardcodes 2-way SMT and is wrong on machines without hyperthreading and
      on 4-way SMT.
    """
    if infra_type:
        report.infrastructure.infra_type = infra_type

    for component in report.infrastructure.components or []:
        component.share = 1
        if component.component_type == "cpu":
            sockets = count_physical_cpus()
            if sockets:
                component.nb_component = int(sockets)


def _extension(
    result: BenchmarkResult,
    model: ModelMetadata,
    facility_pue: Optional[float],
    deployment_id: Optional[str] = None,
    deployment_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the ``llmBenchmark`` block (spec §5.3)."""
    window = result.median_window
    config = result.config
    return {
        "specVersion": SPEC_VERSION,
        "promptSet": f"prompts_{config.prompt_set}",
        "concurrency": config.concurrency,
        "outputTokensPerRequest": config.output_tokens,
        "inputTokenBucket": config.input_bucket,
        "forcedOutputLength": result.forced_output_length,
        "samplingMode": "greedy",
        "warmupRequests": config.warmup_requests,
        "modelRevision": model.revision,
        "activeParametersNumber": model.active_parameters_number,
        "tensorParallelSize": model.tensor_parallel_size,
        "deploymentId": deployment_id,
        "deploymentLabel": deployment_label,
        "nWindows": len(result.windows),
        "relativeSpread": round(result.relative_spread, 6),
        "calibrationDrift": round(result.calibration_drift, 6),
        "ttftP50S": window.ttft_p50_s,
        "tpsPerRequestP50": window.tps_per_request_p50,
        "facilityPue": facility_pue,
        "energyBreakdownKwh": {
            "cpu": window.cpu_energy_kwh,
            "gpu": window.gpu_energy_kwh,
            "ram": window.ram_energy_kwh,
        },
        "perWindowEnergyPerTokenKwh": [w.energy_per_token_kwh for w in result.windows],
    }


def derived_fields(record: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute the quantities of spec §5.4.

    Deliberately a separate function rather than a stored field: the server
    recomputes these from the raw record so the normalization can change
    without invalidating already-submitted data.
    """
    output_tokens = _output_tokens(record)
    energy = record["measures"][0]["powerConsumption"]
    tps = record["llmBenchmark"].get("tpsPerRequestP50") or 0.0
    return {
        "it_energy_per_token": energy / output_tokens if output_tokens else 0.0,
        "latency_per_token_s": 1.0 / tps if tps else 0.0,
    }


def _output_tokens(record: Dict[str, Any]) -> int:
    for entry in record.get("task", {}).get("dataset", []):
        if entry.get("dataUsage") == "output":
            return int(entry.get("dataQuantity", 0))
    return 0


def components_of_type(record: Dict[str, Any], component_type: str) -> List[dict]:
    return [
        c
        for c in record.get("infrastructure", {}).get("components", [])
        if c.get("componentType") == component_type
    ]
