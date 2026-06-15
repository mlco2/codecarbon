"""Collect private product telemetry from tracker state."""

from __future__ import annotations

import importlib.util
import os
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from codecarbon.core.cloud import get_env_cloud_details
from codecarbon.core.gpu import is_nvidia_system
from codecarbon.core.telemetry.schemas import TelemetryLevel
from codecarbon.output_methods.base_output import OutputMethod
from codecarbon.output_methods.emissions_data import EmissionsData

FRAMEWORK_PACKAGES = (
    ("torch", "has_torch"),
    ("transformers", "has_transformers"),
    ("diffusers", "has_diffusers"),
)

OUTPUT_METHOD_LABELS = {
    OutputMethod.CSV: "file",
    OutputMethod.API: "api",
    OutputMethod.LOGGER: "logger",
    OutputMethod.PROMETHEUS: "prometheus",
    OutputMethod.LOGFIRE: "logfire",
}

CI_ENV_VAR_LABELS = (
    ("GITHUB_ACTIONS", "github_actions"),
    ("GITLAB_CI", "gitlab_ci"),
    ("CIRCLECI", "circleci"),
    ("JENKINS_URL", "jenkins"),
    ("CI", "ci"),
)

PACKAGE_MANAGER_ENV = (
    ("UV", "uv"),
    ("POETRY_ACTIVE", "poetry"),
    ("PIP_RUN", "pip"),
)


@dataclass
class TelemetryContext:
    """Snapshot of tracker state used to build a telemetry payload."""

    conf: dict[str, Any]
    emissions: EmissionsData
    hardware: list[Any]
    resource_tracker: Any
    output_methods: list[str]
    tasks: dict[str, Any]
    measure_power_secs: float | None
    integration: str

    @classmethod
    def from_tracker(cls, tracker: Any, emissions: EmissionsData) -> TelemetryContext:
        """Build a context snapshot from an active emissions tracker."""
        from codecarbon.emissions_tracker import OfflineEmissionsTracker

        methods = [
            OUTPUT_METHOD_LABELS[method]
            for method in getattr(tracker, "_output_methods", None) or []
            if method in OUTPUT_METHOD_LABELS
        ]
        if getattr(tracker, "_emissions_endpoint", None):
            methods.append("http")

        argv = " ".join(sys.argv)
        if isinstance(tracker, OfflineEmissionsTracker):
            integration = "offline_tracker"
        elif "codecarbon" in argv and "monitor" in argv:
            integration = "cli_monitor"
        else:
            integration = "library"

        return cls(
            conf=getattr(tracker, "_conf", {}),
            emissions=emissions,
            hardware=getattr(tracker, "_hardware", []) or [],
            resource_tracker=getattr(tracker, "_resource_tracker", None),
            output_methods=methods,
            tasks=getattr(tracker, "_tasks", {}) or {},
            measure_power_secs=getattr(tracker, "_measure_power_secs", None),
            integration=integration,
        )


def _strip_empty(data: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in data.items()
        if value not in (None, "", [], {})
    }


def _env_label(env_vars: tuple[tuple[str, str], ...]) -> str | None:
    return next((label for var, label in env_vars if os.environ.get(var)), None)


def _package_installed(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _round_coordinate(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 1)


def _cloud_region(emissions: EmissionsData) -> tuple[str | None, str | None, str | None]:
    details = get_env_cloud_details()
    raw_provider = raw_region = None
    if details and details.get("metadata"):
        provider = (details.get("provider") or "").lower() or None
        metadata = details.get("metadata") or {}
        if provider == "aws":
            raw_region = metadata.get("region")
        elif provider == "azure":
            raw_region = (metadata.get("compute") or {}).get("location")
        elif provider == "gcp":
            zone = metadata.get("zone") or ""
            parts = zone.split("/")
            raw_region = parts[-1].rsplit("-", 1)[0] if parts else None
        raw_provider = provider

    cloud_provider = emissions.cloud_provider or raw_provider
    cloud_region = emissions.cloud_region or raw_region
    region = emissions.region
    if emissions.on_cloud == "Y" and cloud_region:
        region = region or cloud_region
    return cloud_provider, cloud_region, region


def _detect_python_env_type() -> str | None:
    if os.environ.get("CONDA_DEFAULT_ENV"):
        return "conda"
    if os.environ.get("VIRTUAL_ENV"):
        return "venv"
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        return "venv"
    return "system"


def _detect_codecarbon_install_method() -> str | None:
    try:
        from importlib.metadata import distribution

        dist = distribution("codecarbon")
        if getattr(dist, "editable", False):
            return "editable"
        installer = (dist.metadata.get("Installer") or "").lower()
        if "uv" in installer:
            return "uv"
        if "pip" in installer:
            return "pip"
    except Exception:
        pass
    return None


def _detect_notebook_environment() -> str | None:
    if os.environ.get("COLAB_GPU") is not None or "google.colab" in sys.modules:
        return "colab"
    try:
        from IPython import get_ipython

        if "ZMQInteractiveShell" in get_ipython().__class__.__name__:
            return "jupyter"
    except Exception:
        pass
    return None


def _container_info() -> tuple[bool | None, str | None]:
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        return True, "kubernetes"
    if os.path.exists("/.dockerenv"):
        return True, "docker"
    return None, None


def _detect_ide() -> str | None:
    if os.environ.get("CURSOR_TRACE_ID") or os.environ.get("CURSOR_SESSION"):
        return "cursor"
    if os.environ.get("VSCODE_PID") or os.environ.get("TERM_PROGRAM") == "vscode":
        return "vscode"
    if os.environ.get("PYCHARM_HOSTED"):
        return "pycharm"
    return None


def _cudnn_version() -> str | None:
    if not _package_installed("torch"):
        return None
    try:
        import torch

        version = torch.backends.cudnn.version()
        return str(version) if version is not None else None
    except Exception:
        return None


def _gpu_static_fields() -> dict[str, Any]:
    if not is_nvidia_system():
        return {}
    try:
        import pynvml

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        cuda_version = pynvml.nvmlSystemGetCudaDriverVersion_v2()
        if isinstance(cuda_version, int):
            cuda_version = f"{cuda_version // 1000}.{(cuda_version % 1000) // 10}"
        return {
            "gpu_memory_total_gb": mem.total / (1024**3),
            "gpu_driver_version": pynvml.nvmlSystemGetDriverVersion(),
            "cuda_version": cuda_version,
        }
    except Exception:
        return {}


def _hardware_diagnostics(ctx: TelemetryContext) -> dict[str, Any]:
    from codecarbon.core import cpu

    hardware_tracked: list[str] = []
    for item in ctx.hardware:
        try:
            hardware_tracked.append(item.description())
        except Exception:
            pass
    gpu_detection_method = None
    if ctx.resource_tracker is not None:
        gpu_tracker = getattr(ctx.resource_tracker, "gpu_tracker", None)
        if gpu_tracker and gpu_tracker != "Unspecified":
            gpu_detection_method = gpu_tracker

    rapl_available = cpu.is_rapl_available() if platform.system() == "Linux" else None
    return {
        "hardware_tracked": hardware_tracked or None,
        "hardware_detection_success": bool(hardware_tracked),
        "rapl_available": rapl_available,
        "gpu_detection_method": gpu_detection_method,
        "api_mode": "online" if "api" in ctx.output_methods else "offline",
    }


def _minimal_payload(ctx: TelemetryContext, level: TelemetryLevel) -> dict[str, Any]:
    """Fields allowed for ``telemetry_level=minimal`` (matches DB + MINIMAL_TELEMETRY_FIELDS)."""
    conf = ctx.conf
    emissions = ctx.emissions
    cloud_provider, cloud_region, region = _cloud_region(emissions)
    region = region or conf.get("region")

    payload = {
        "timestamp": datetime.now(timezone.utc),
        "telemetry_level": level.value,
        "os": conf.get("os") or platform.platform(),
        "country_name": emissions.country_name,
        "country_iso_code": emissions.country_iso_code,
        "region": region,
        "cloud_provider": cloud_provider,
        "cloud_region": cloud_region,
        "longitude": _round_coordinate(conf.get("longitude", emissions.longitude)),
        "latitude": _round_coordinate(conf.get("latitude", emissions.latitude)),
        "cpu_count": conf.get("cpu_count"),
        "cpu_physical_count": conf.get("cpu_physical_count"),
        "cpu_model": conf.get("cpu_model"),
        "cpu_architecture": platform.machine(),
        "gpu_count": conf.get("gpu_count"),
        "gpu_model": conf.get("gpu_model"),
        "ram_total_size_gb": conf.get("ram_total_size"),
        "python_version": conf.get("python_version") or platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_env_type": _detect_python_env_type(),
        "codecarbon_version": conf.get("codecarbon_version"),
        "codecarbon_install_method": _detect_codecarbon_install_method(),
        "cudnn_version": _cudnn_version(),
        **_gpu_static_fields(),
    }
    return _strip_empty(payload)


def _extensive_payload(ctx: TelemetryContext) -> dict[str, Any]:
    """Extra fields stored only for ``telemetry_level=extensive``."""
    emissions = ctx.emissions
    in_container, container_runtime = _container_info()
    framework_fields = {
        has_field: _package_installed(package)
        for package, has_field in FRAMEWORK_PACKAGES
    }

    return _strip_empty(
        {
            "tracking_mode": ctx.conf.get("tracking_mode"),
            "decorator_vs_context": ctx.integration,
            "output_methods": ctx.output_methods or None,
            "task_tracking_used": bool(ctx.tasks),
            "measure_power_interval_secs": ctx.measure_power_secs,
            "python_package_manager": _env_label(PACKAGE_MANAGER_ENV),
            "in_container": in_container,
            "container_runtime": container_runtime,
            "ci_environment": _env_label(CI_ENV_VAR_LABELS),
            "notebook_environment": _detect_notebook_environment(),
            "ide_used": _detect_ide(),
            "duration_seconds": float(emissions.duration)
            if emissions.duration
            else None,
            "total_emissions_kg": emissions.emissions,
            "emissions_rate_kg_per_sec": emissions.emissions_rate,
            "energy_consumed_kwh": emissions.energy_consumed,
            "cpu_energy_kwh": emissions.cpu_energy,
            "gpu_energy_kwh": emissions.gpu_energy,
            "ram_energy_kwh": emissions.ram_energy,
            "cpu_utilization_avg": emissions.cpu_utilization_percent,
            "gpu_utilization_avg": emissions.gpu_utilization_percent,
            "ram_utilization_avg": emissions.ram_utilization_percent,
            **framework_fields,
            **_hardware_diagnostics(ctx),
        }
    )


def build_payload(
    ctx: TelemetryContext,
    level: TelemetryLevel = TelemetryLevel.minimal,
) -> dict[str, Any]:
    """Build a validated telemetry payload dict for ``POST /telemetry``."""
    payload = _minimal_payload(ctx, level)
    if level == TelemetryLevel.extensive:
        payload.update(_extensive_payload(ctx))
    return payload
