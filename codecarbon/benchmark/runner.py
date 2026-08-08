"""
Measurement loop for the LLM energy benchmark.

Implements spec §3: calibration, warmup, repeated steady-state windows, and the
repeatability check across windows. Energy comes from CodeCarbon's task API
(``start_task`` / ``stop_task``), which yields the isolated delta for each
window.
"""

import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import List, Optional

from codecarbon.benchmark.backends import Backend, BackendInfo, GenerationResult
from codecarbon.benchmark.prompts import build_prompts
from codecarbon.external.logger import logger
from codecarbon.output_methods.emissions_data import EmissionsData


@dataclass
class BenchmarkConfig:
    """Everything that defines a single benchmark configuration (spec §4.2)."""

    model: str
    concurrency: int
    output_tokens: int = 256
    input_bucket: int = 128
    n_windows: int = 3
    warmup_requests: int = 8
    calibration_seconds: float = 30.0
    measure_power_secs: int = 5
    prompt_set: str = "v1"
    # Thresholds from the spec; overridable so the gates can be relaxed
    # deliberately and visibly rather than by accident.
    min_window_seconds: float = 120.0
    min_output_tokens: int = 5000
    max_relative_spread: float = 0.15
    max_calibration_drift: float = 0.10


@dataclass
class WindowResult:
    """One steady-state measurement window."""

    duration_s: float
    n_requests: int
    input_tokens: int
    output_tokens: int
    cpu_energy_kwh: float
    gpu_energy_kwh: float
    ram_energy_kwh: float
    cpu_utilization_percent: float
    gpu_utilization_percent: float
    ttft_p50_s: Optional[float]
    tps_per_request_p50: float
    short_requests: int
    emissions_data: EmissionsData

    @property
    def energy_kwh(self) -> float:
        return self.cpu_energy_kwh + self.gpu_energy_kwh + self.ram_energy_kwh

    @property
    def energy_per_token_kwh(self) -> float:
        if self.output_tokens <= 0:
            return 0.0
        return self.energy_kwh / self.output_tokens


@dataclass
class BenchmarkResult:
    """Outcome of a full configuration: every window plus the derived checks."""

    config: BenchmarkConfig
    backend_info: BackendInfo
    windows: List[WindowResult]
    median_window: WindowResult
    relative_spread: float
    calibration_kwh: float
    calibration_duration_s: float
    calibration_drift: float
    forced_output_length: bool
    cpu_tracking_mode: Optional[str] = None
    gpu_tracking_mode: Optional[str] = None
    gate_failures: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.gate_failures


def _percentile(values: List[float], pct: float) -> Optional[float]:
    clean = sorted(v for v in values if v is not None)
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    index = min(int(len(clean) * pct), len(clean) - 1)
    return clean[index]


def _drive(
    backend: Backend,
    prompts: List[str],
    concurrency: int,
    output_tokens: int,
) -> List[GenerationResult]:
    """Issue every prompt, keeping ``concurrency`` requests in flight."""
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(backend.generate, prompt, output_tokens) for prompt in prompts
        ]
        return [f.result() for f in futures]


def _make_tracker(config: BenchmarkConfig, country_iso_code: Optional[str]):
    """
    Build a tracker configured for benchmarking.

    PUE is pinned to 1.0: spec §3.1 requires PUE-free energy, and CodeCarbon
    multiplies PUE into every hardware sample (``emissions_tracker.py:1178``),
    which would silently inflate the record with no field to record it.
    """
    from codecarbon.emissions_tracker import EmissionsTracker, OfflineEmissionsTracker

    kwargs = dict(
        project_name="codecarbon-llm-benchmark",
        measure_power_secs=config.measure_power_secs,
        # No output methods: the harness emits its own BoAmps record and must
        # not also write emissions.csv or push to the API.
        output_methods=[],
        allow_multiple_runs=True,
        log_level="error",
        pue=1.0,
    )
    if country_iso_code:
        tracker = OfflineEmissionsTracker(country_iso_code=country_iso_code, **kwargs)
    else:
        tracker = EmissionsTracker(**kwargs)

    if getattr(tracker, "_pue", 1.0) != 1.0:
        raise ValueError(
            f"Benchmark requires PUE=1.0 but the tracker resolved PUE="
            f"{tracker._pue}. Remove `pue` from your .codecarbon.config; the "
            "facility PUE belongs in llmBenchmark.facilityPue, not folded into "
            "the energy figure (spec §3.1)."
        )
    return tracker


def _window_from(
    data: EmissionsData, results: List[GenerationResult], output_tokens: int
) -> WindowResult:
    latencies_per_token = [
        r.latency_s / r.output_tokens for r in results if r.output_tokens > 0
    ]
    median_latency_per_token = (
        statistics.median(latencies_per_token) if latencies_per_token else 0.0
    )
    return WindowResult(
        duration_s=data.duration,
        n_requests=len(results),
        input_tokens=sum(r.input_tokens for r in results),
        output_tokens=sum(r.output_tokens for r in results),
        cpu_energy_kwh=data.cpu_energy,
        gpu_energy_kwh=data.gpu_energy,
        ram_energy_kwh=data.ram_energy,
        cpu_utilization_percent=data.cpu_utilization_percent,
        gpu_utilization_percent=data.gpu_utilization_percent,
        ttft_p50_s=_percentile([r.ttft_s for r in results], 0.5),
        tps_per_request_p50=(
            1.0 / median_latency_per_token if median_latency_per_token else 0.0
        ),
        short_requests=sum(1 for r in results if not r.length_capped),
        emissions_data=data,
    )


def _size_window(config: BenchmarkConfig, observed_tps: float) -> int:
    """
    Choose the request count so a window clears both §3.7 minimums.

    Sized from throughput observed during warmup rather than guessed, then
    padded by 20% so a slightly slower steady state still clears the bar.
    """
    for_tokens = config.min_output_tokens / config.output_tokens
    for_duration = (
        (config.min_window_seconds * observed_tps) / config.output_tokens
        if observed_tps > 0
        else for_tokens
    )
    needed = max(for_tokens, for_duration, config.concurrency)
    return max(config.concurrency, int(needed * 1.2) + 1)


def run_benchmark(
    backend: Backend,
    config: BenchmarkConfig,
    country_iso_code: Optional[str] = None,
) -> BenchmarkResult:
    """Run one configuration end to end and return its measured result."""
    backend_info = backend.info()
    tracker = _make_tracker(config, country_iso_code)
    prompt_cursor = 0

    try:
        # --- §3.3 residency + §3.5 warmup -------------------------------
        logger.info("Warmup: %d requests", config.warmup_requests)
        warmup_prompts = build_prompts(
            config.warmup_requests,
            config.input_bucket,
            config.prompt_set,
            start_index=prompt_cursor,
        )
        prompt_cursor += config.warmup_requests
        warmup_start = time.perf_counter()
        warmup_results = _drive(
            backend, warmup_prompts, config.concurrency, config.output_tokens
        )
        warmup_elapsed = time.perf_counter() - warmup_start
        warmup_tokens = sum(r.output_tokens for r in warmup_results)
        observed_tps = warmup_tokens / warmup_elapsed if warmup_elapsed > 0 else 0.0
        logger.info("Warmup throughput: %.1f output tokens/s", observed_tps)

        # --- §3.4 calibration, before ------------------------------------
        calibration_before = _calibrate(tracker, config, "calibration-pre")

        # --- §3.7/§3.8 measurement windows -------------------------------
        n_requests = _size_window(config, observed_tps)
        logger.info(
            "Measuring %d windows of %d requests at concurrency %d",
            config.n_windows,
            n_requests,
            config.concurrency,
        )

        windows: List[WindowResult] = []
        for i in range(config.n_windows):
            prompts = build_prompts(
                n_requests,
                config.input_bucket,
                config.prompt_set,
                start_index=prompt_cursor,
            )
            prompt_cursor += n_requests

            tracker.start_task(f"window-{i}")
            results = _drive(backend, prompts, config.concurrency, config.output_tokens)
            data = tracker.stop_task()

            window = _window_from(data, results, config.output_tokens)
            windows.append(window)
            logger.info(
                "Window %d: %.1fs, %d tokens, %.3e kWh/token",
                i,
                window.duration_s,
                window.output_tokens,
                window.energy_per_token_kwh,
            )

        # --- §3.4 calibration, after -------------------------------------
        calibration_after = _calibrate(tracker, config, "calibration-post")
        cpu_mode, gpu_mode = _tracking_modes(tracker)
    finally:
        try:
            tracker.stop()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Tracker stop failed: %s", exc)

    return _summarise(
        config,
        backend_info,
        windows,
        calibration_before,
        calibration_after,
        cpu_mode,
        gpu_mode,
    )


def _tracking_modes(tracker):
    """
    Read how each hardware component is being measured.

    Spec §5.2 requires cpuTrackingMode/gpuTrackingMode, and CodeCarbon's BoAmps
    exporter omits them (``mapper.py:116-119``) because ``EmissionsData`` does
    not carry them. They are read straight off the hardware objects here.
    RAPL versus constant-power estimation is the difference between a
    measurement and a guess, and a curator cannot tell them apart otherwise.
    """
    from codecarbon.external.hardware import CPU, GPU

    cpu_mode = None
    gpu_mode = None
    for hardware in getattr(tracker, "_hardware", []) or []:
        if isinstance(hardware, CPU):
            cpu_mode = getattr(hardware, "_mode", None)
        elif isinstance(hardware, GPU):
            # CodeCarbon reads GPUs through NVML exclusively.
            gpu_mode = "nvml"
    return cpu_mode, gpu_mode


def _calibrate(tracker, config: BenchmarkConfig, name: str) -> WindowResult:
    """Measure idle-with-model-loaded energy (spec §3.4)."""
    logger.info("Calibration (%s): %.0fs idle", name, config.calibration_seconds)
    tracker.start_task(name)
    time.sleep(config.calibration_seconds)
    data = tracker.stop_task()
    return _window_from(data, [], config.output_tokens)


def _summarise(
    config: BenchmarkConfig,
    backend_info: BackendInfo,
    windows: List[WindowResult],
    calibration_before: WindowResult,
    calibration_after: WindowResult,
    cpu_tracking_mode: Optional[str] = None,
    gpu_tracking_mode: Optional[str] = None,
) -> BenchmarkResult:
    per_token = [w.energy_per_token_kwh for w in windows]
    median = statistics.median(per_token)
    spread = (max(per_token) - min(per_token)) / median if median > 0 else float("inf")

    # Emit the raw numbers of the window whose per-token energy is the median,
    # so energy, duration and token counts in the record stay mutually
    # consistent. Averaging them would produce a record describing no real run.
    order = sorted(windows, key=lambda w: w.energy_per_token_kwh)
    median_window = order[(len(order) - 1) // 2]

    before = calibration_before.energy_kwh / max(calibration_before.duration_s, 1e-9)
    after = calibration_after.energy_kwh / max(calibration_after.duration_s, 1e-9)
    drift = abs(after - before) / before if before > 0 else 0.0

    short = sum(w.short_requests for w in windows)
    forced = backend_info.supports_forced_output_length and short == 0

    failures: List[str] = []
    if spread > config.max_relative_spread:
        failures.append(
            f"repeatability: spread {spread:.1%} exceeds "
            f"{config.max_relative_spread:.0%} (§3.8)"
        )
    if drift > config.max_calibration_drift:
        failures.append(
            f"calibration drift {drift:.1%} exceeds "
            f"{config.max_calibration_drift:.0%} — background load (§3.2)"
        )
    if median_window.duration_s < config.min_window_seconds:
        failures.append(
            f"window {median_window.duration_s:.0f}s below "
            f"{config.min_window_seconds:.0f}s minimum (§3.7)"
        )
    if median_window.output_tokens < config.min_output_tokens:
        failures.append(
            f"{median_window.output_tokens} output tokens below "
            f"{config.min_output_tokens} minimum (§3.7)"
        )
    if not forced:
        failures.append(
            f"output length not forced: backend "
            f"supports_forced_output_length="
            f"{backend_info.supports_forced_output_length}, "
            f"{short} request(s) stopped before the cap (§3.6)"
        )

    return BenchmarkResult(
        config=config,
        backend_info=backend_info,
        windows=windows,
        median_window=median_window,
        relative_spread=spread,
        calibration_kwh=calibration_before.energy_kwh,
        calibration_duration_s=calibration_before.duration_s,
        calibration_drift=drift,
        forced_output_length=forced,
        cpu_tracking_mode=cpu_tracking_mode,
        gpu_tracking_mode=gpu_tracking_mode,
        gate_failures=failures,
    )
