"""
Validity rules for benchmark records (spec §6).

These are the mechanical rejection rules the ingestion endpoint will run. They
are implemented here so the harness can apply them locally before a record is
ever uploaded — a failure is much cheaper to find on the machine that produced
it.

Passing validation is not approval: publication into the curated reference
snapshot still requires human review (spec §8.3).
"""

from typing import Any, Dict, List

SPEC_VERSION = "1.0.0-draft"
KNOWN_SPEC_VERSIONS = {SPEC_VERSION}

MIN_WINDOW_SECONDS = 120.0
MIN_OUTPUT_TOKENS = 5000
MAX_RELATIVE_SPREAD = 0.15
MIN_WINDOWS = 3
MIN_WARMUP_REQUESTS = 8
MIN_GPU_UTILIZATION = 0.7
MAX_MEAN_POWER_W = 2000.0
ENERGY_SUM_TOLERANCE = 0.01

# Kept in step with codecarbon.benchmark.record.QUANTIZATIONS. Imported rather
# than duplicated would be circular (record imports this module for the spec
# version), so the pair is asserted equal by a test.
REQUIRED_QUANTIZATIONS = (
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


class ValidationError(Exception):
    """Raised when a record fails the §6 rules."""

    def __init__(self, failures: List[str]):
        self.failures = failures
        super().__init__("; ".join(failures))


def _dataset_quantity(record: Dict[str, Any], usage: str) -> float:
    for entry in record.get("task", {}).get("dataset", []) or []:
        if entry.get("dataUsage") == usage:
            return float(entry.get("dataQuantity") or 0)
    return 0.0


def _components(record: Dict[str, Any]) -> List[dict]:
    return record.get("infrastructure", {}).get("components", []) or []


def validate_record(record: Dict[str, Any]) -> List[str]:
    """
    Apply the §6 rules and return a list of failures (empty when valid).

    Rule 1 — BoAmps schema validation itself — is not reimplemented here; run
    ``BoAmps/tools/schema_validator/`` for that. The §5.2 profile constraints
    that schema validation cannot express are checked below.
    """
    failures: List[str] = []
    ext = record.get("llmBenchmark") or {}
    measures = record.get("measures") or [{}]
    measure = measures[0]

    # Rule 8 first: an unknown spec version makes every other rule suspect.
    if ext.get("specVersion") not in KNOWN_SPEC_VERSIONS:
        failures.append(f"rule 8: unknown specVersion {ext.get('specVersion')!r}")

    # Rule 1 (profile constraints expressible here)
    task = record.get("task") or {}
    if task.get("taskStage") != "inference":
        failures.append("rule 1: task.taskStage must be 'inference'")
    algorithms = task.get("algorithms") or [{}]
    algorithm = algorithms[0]
    if algorithm.get("algorithmType") != "llm":
        failures.append("rule 1: task.algorithms[0].algorithmType must be 'llm'")
    if not algorithm.get("foundationModelName"):
        failures.append("rule 1: task.algorithms[0].foundationModelName is required")
    if algorithm.get("quantization") not in REQUIRED_QUANTIZATIONS:
        failures.append(
            f"rule 1: quantization must be one of "
            f"{', '.join(REQUIRED_QUANTIZATIONS)}"
        )
    if not algorithm.get("frameworkVersion"):
        failures.append("rule 1: task.algorithms[0].frameworkVersion is required")
    if not measure.get("cpuTrackingMode"):
        failures.append("rule 1: measures[0].cpuTrackingMode is required")
    publisher = (record.get("header") or {}).get("publisher") or {}
    if publisher.get("confidentialityLevel") != "public":
        failures.append(
            "rule 1: header.publisher.confidentialityLevel must be 'public' — "
            "a record that cannot be republished is not reference data"
        )
    if not (record.get("header") or {}).get("licensing"):
        failures.append("rule 1: header.licensing is required")

    gpu_components = [c for c in _components(record) if c.get("componentType") == "gpu"]
    if gpu_components and not measure.get("gpuTrackingMode"):
        failures.append("rule 1: measures[0].gpuTrackingMode is required with a GPU")

    # Rule 2 — window minimums
    duration = float(measure.get("measurementDuration") or 0)
    output_tokens = _dataset_quantity(record, "output")
    if duration < MIN_WINDOW_SECONDS:
        failures.append(
            f"rule 2: measurementDuration {duration:.0f}s < {MIN_WINDOW_SECONDS:.0f}s"
        )
    if output_tokens < MIN_OUTPUT_TOKENS:
        failures.append(
            f"rule 2: output dataQuantity {output_tokens:.0f} < {MIN_OUTPUT_TOKENS}"
        )

    # Rule 3 — repetitions
    if int(ext.get("nWindows") or 0) < MIN_WINDOWS:
        failures.append(f"rule 3: nWindows {ext.get('nWindows')} < {MIN_WINDOWS}")
    spread = ext.get("relativeSpread")
    if spread is None or float(spread) > MAX_RELATIVE_SPREAD:
        failures.append(
            f"rule 3: relativeSpread {spread} exceeds {MAX_RELATIVE_SPREAD}"
        )

    # Rule 4 — warmup
    if int(ext.get("warmupRequests") or 0) < MIN_WARMUP_REQUESTS:
        failures.append(
            f"rule 4: warmupRequests {ext.get('warmupRequests')} "
            f"< {MIN_WARMUP_REQUESTS}"
        )

    # Rule 5 — forced output length
    if ext.get("forcedOutputLength") is not True:
        failures.append("rule 5: forcedOutputLength must be true (§3.6)")

    # Rules 6 and 7 — energy breakdown
    breakdown = ext.get("energyBreakdownKwh") or {}
    power_consumption = float(measure.get("powerConsumption") or 0)
    if gpu_components and float(breakdown.get("gpu") or 0) == 0:
        failures.append(
            "rule 6: gpu energy is 0 with a GPU declared — NVML unavailable "
            "rather than zero consumption"
        )
    breakdown_sum = sum(float(breakdown.get(k) or 0) for k in ("cpu", "gpu", "ram"))
    if power_consumption > 0:
        deviation = abs(breakdown_sum - power_consumption) / power_consumption
        if deviation > ENERGY_SUM_TOLERANCE:
            failures.append(
                f"rule 7: energyBreakdownKwh sums to {breakdown_sum:.6g}, "
                f"powerConsumption is {power_consumption:.6g} "
                f"({deviation:.1%} apart)"
            )

    # Rule 9 — dedicated hardware
    for component in _components(record):
        if component.get("share") != 1:
            failures.append(
                f"rule 9: component {component.get('componentType')} has "
                f"share={component.get('share')}; v1 accepts dedicated "
                "hardware only"
            )

    # Rule 10 — implied mean power plausibility
    if duration > 0 and power_consumption > 0:
        mean_power_w = power_consumption * 3.6e6 / duration
        calibration_kwh = float(measure.get("powerCalibrationMeasurement") or 0)
        calibration_duration = float(measure.get("durationCalibrationMeasurement") or 0)
        floor_w = (
            calibration_kwh * 3.6e6 / calibration_duration
            if calibration_duration > 0
            else 0.0
        )
        if mean_power_w < floor_w or mean_power_w > MAX_MEAN_POWER_W:
            failures.append(
                f"rule 10: implied mean power {mean_power_w:.0f}W outside "
                f"[{floor_w:.0f}W, {MAX_MEAN_POWER_W:.0f}W]"
            )

    # Rule 11 — GPU actually doing the work
    gpu_utilization = measure.get("averageUtilizationGpu")
    if gpu_components and gpu_utilization is not None:
        if float(gpu_utilization) < MIN_GPU_UTILIZATION:
            failures.append(
                f"rule 11: averageUtilizationGpu {gpu_utilization} < "
                f"{MIN_GPU_UTILIZATION} — the measurement is dominated by "
                "something other than generation"
            )

    return failures


def assert_valid(record: Dict[str, Any]) -> None:
    """Raise :class:`ValidationError` if the record fails any §6 rule."""
    failures = validate_record(record)
    if failures:
        raise ValidationError(failures)
