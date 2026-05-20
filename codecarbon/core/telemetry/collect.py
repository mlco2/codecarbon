"""Collect private product telemetry (Tier 1 / Tier 2) from tracker state."""

from __future__ import annotations

import importlib.util
import os
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from codecarbon.core.cloud import get_env_cloud_details
from codecarbon.core.gpu import is_nvidia_system
from codecarbon.core.telemetry.schemas import PRIVATE_TELEMETRY_FIELDS, TelemetryLevel
from codecarbon.output_methods.emissions_data import EmissionsData

FRAMEWORK_PACKAGES = (
    ("torch", "has_torch"),
    ("transformers", "has_transformers"),
    ("diffusers", "has_diffusers"),
    ("sklearn", "has_sklearn"),
)

PACKAGE_MANAGER_ENV = (
    ("UV", "uv"),
    ("POETRY_ACTIVE", "poetry"),
    ("PIP_RUN", "pip"),
)

CI_ENVIRONMENTS = (
    ("GITHUB_ACTIONS", "github_actions"),
    ("GITLAB_CI", "gitlab_ci"),
    ("CIRCLECI", "circleci"),
    ("JENKINS_URL", "jenkins"),
    ("CI", "ci"),
)

CONTAINER_RUNTIME_ENV = (
    ("KUBERNETES_SERVICE_HOST", "kubernetes"),
)

OUTPUT_METHOD_FIELDS = (
    ("save_to_file", "file"),
    ("save_to_api", "api"),
    ("save_to_logger", "logger"),
    ("emissions_endpoint", "http"),
    ("save_to_prometheus", "prometheus"),
    ("save_to_logfire", "logfire"),
)


@dataclass
class TelemetryContext:
    """Snapshot of tracker state used to build a telemetry payload."""

    conf: dict[str, Any]
    emissions: EmissionsData
    hardware: list[Any]
    resource_tracker: Any
    save_to_api: bool
    save_to_file: bool
    save_to_logger: bool
    save_to_prometheus: bool
    save_to_logfire: bool
    emissions_endpoint: str | None
    tasks: dict[str, Any]
    measure_power_secs: float | None
    is_offline: bool

    @classmethod
    def from_tracker(cls, tracker: Any, emissions: EmissionsData) -> TelemetryContext:
        """Build a context snapshot from an active emissions tracker.

        Args:
            tracker: Active emissions tracker instance.
            emissions: Run emissions data.

        Returns:
            Context for ``build_payload``.
        """
        from codecarbon.emissions_tracker import OfflineEmissionsTracker

        return cls(
            conf=getattr(tracker, "_conf", {}),
            emissions=emissions,
            hardware=getattr(tracker, "_hardware", []) or [],
            resource_tracker=getattr(tracker, "_resource_tracker", None),
            save_to_api=bool(getattr(tracker, "_save_to_api", False)),
            save_to_file=bool(getattr(tracker, "_save_to_file", False)),
            save_to_logger=bool(getattr(tracker, "_save_to_logger", False)),
            save_to_prometheus=bool(getattr(tracker, "_save_to_prometheus", False)),
            save_to_logfire=bool(getattr(tracker, "_save_to_logfire", False)),
            emissions_endpoint=getattr(tracker, "_emissions_endpoint", None),
            tasks=getattr(tracker, "_tasks", {}) or {},
            measure_power_secs=getattr(tracker, "_measure_power_secs", None),
            is_offline=isinstance(tracker, OfflineEmissionsTracker),
        )


def _non_empty(value: Any) -> bool:
    return value not in (None, "", [], {})


def _strip_none(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if _non_empty(value)}


def _first_env_match(mapping: tuple[tuple[str, str], ...]) -> Optional[str]:
    return next((label for var, label in mapping if os.environ.get(var)), None)


def _package_installed(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _detect_codecarbon_install_method() -> Optional[str]:
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


def _detect_python_env_type() -> Optional[str]:
    if os.environ.get("CONDA_DEFAULT_ENV"):
        return "conda"
    if os.environ.get("VIRTUAL_ENV"):
        return "venv"
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        return "venv"
    return "system"


def _detect_notebook_environment() -> Optional[str]:
    if os.environ.get("COLAB_GPU") is not None or "google.colab" in sys.modules:
        return "colab"
    try:
        from IPython import get_ipython

        shell = get_ipython().__class__.__name__
        if "ZMQInteractiveShell" in shell:
            return "jupyter"
    except Exception:
        pass
    return None


def _container_info() -> tuple[bool, Optional[str]]:
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        return True, "kubernetes"
    if os.path.exists("/.dockerenv"):
        return True, "docker"
    return False, None


def _detect_ide() -> Optional[str]:
    if os.environ.get("CURSOR_TRACE_ID") or os.environ.get("CURSOR_SESSION"):
        return "cursor"
    if os.environ.get("VSCODE_PID") or os.environ.get("TERM_PROGRAM") == "vscode":
        return "vscode"
    if os.environ.get("PYCHARM_HOSTED"):
        return "pycharm"
    return None


def _cudnn_version() -> Optional[str]:
    if not _package_installed("torch"):
        return None
    try:
        import torch

        version = torch.backends.cudnn.version()
        return str(version) if version is not None else None
    except Exception:
        return None


def _collect_hardware_diagnostics(ctx: TelemetryContext) -> dict[str, Any]:
    from codecarbon.core import cpu

    hardware_tracked: list[str] = []
    for item in ctx.hardware:
        try:
            hardware_tracked.append(item.description())
        except Exception:
            pass

    gpu_detection_method: Optional[str] = None
    if ctx.resource_tracker is not None:
        gpu_tracker = getattr(ctx.resource_tracker, "gpu_tracker", None)
        if gpu_tracker and gpu_tracker != "Unspecified":
            gpu_detection_method = gpu_tracker

    rapl_available: Optional[bool] = None
    if platform.system() == "Linux":
        rapl_available = cpu.is_rapl_available()

    return {
        "hardware_tracked": hardware_tracked or None,
        "hardware_detection_success": bool(hardware_tracked),
        "rapl_available": rapl_available,
        "gpu_detection_method": gpu_detection_method,
        "api_mode": "online" if ctx.save_to_api else "offline",
    }


def _detect_integration_surface(ctx: TelemetryContext) -> str:
    if ctx.is_offline:
        return "offline_tracker"
    argv = " ".join(sys.argv)
    if "codecarbon" in argv and "monitor" in argv:
        return "cli_monitor"
    return "library"


def _collect_output_methods(ctx: TelemetryContext) -> list[str]:
    methods: list[str] = []
    for field_name, label in OUTPUT_METHOD_FIELDS:
        value = getattr(ctx, field_name)
        if field_name == "emissions_endpoint":
            if value:
                methods.append(label)
        elif value:
            methods.append(label)
    return methods


def _raw_cloud_provider_and_region() -> tuple[Optional[str], Optional[str]]:
    details = get_env_cloud_details()
    if not details or not details.get("metadata"):
        return None, None
    provider = (details.get("provider") or "").lower() or None
    metadata = details.get("metadata") or {}
    region: Optional[str] = None
    if provider == "aws":
        region = metadata.get("region")
    elif provider == "azure":
        region = (metadata.get("compute") or {}).get("location")
    elif provider == "gcp":
        zone = metadata.get("zone") or ""
        parts = zone.split("/")
        region = parts[-1].rsplit("-", 1)[0] if parts else None
    return provider, region


def _collect_framework_fields() -> dict[str, Any]:
    return {
        has_field: _package_installed(package)
        for package, has_field in FRAMEWORK_PACKAGES
    }


def _gpu_static_fields() -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if not is_nvidia_system():
        return fields
    try:
        import pynvml

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        fields["gpu_memory_total_gb"] = mem.total / (1024**3)
        fields["gpu_driver_version"] = pynvml.nvmlSystemGetDriverVersion()
        fields["cuda_version"] = pynvml.nvmlSystemGetCudaDriverVersion_v2()
        if isinstance(fields["cuda_version"], int):
            v = fields["cuda_version"]
            fields["cuda_version"] = f"{v // 1000}.{(v % 1000) // 10}"
    except Exception:
        pass
    return fields


def build_payload(
    ctx: TelemetryContext,
    level: TelemetryLevel = TelemetryLevel.minimal,
) -> dict[str, Any]:
    """Build a private telemetry payload dict for ``POST /telemetry``.

    Args:
        ctx: Tracker snapshot from ``TelemetryContext.from_tracker``.
        level: Resolved ``TelemetryLevel`` (``minimal`` or ``extensive``).

    Returns:
        Payload dict for ``TelemetryCreate``.
    """
    emissions = ctx.emissions
    conf = ctx.conf
    raw_provider, raw_region = _raw_cloud_provider_and_region()
    on_cloud = emissions.on_cloud == "Y"
    cloud_provider = emissions.cloud_provider or raw_provider
    cloud_region = emissions.cloud_region or raw_region
    region = emissions.region or conf.get("region")
    if on_cloud and cloud_region:
        region = region or cloud_region

    integration_surface = _detect_integration_surface(ctx)
    in_container, container_runtime = _container_info()
    gpu_fields = _gpu_static_fields()

    raw: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc),
        "os": conf.get("os") or platform.platform(),
        "python_version": conf.get("python_version") or platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_env_type": _detect_python_env_type(),
        "python_package_manager": _first_env_match(PACKAGE_MANAGER_ENV),
        "codecarbon_version": conf.get("codecarbon_version"),
        "codecarbon_install_method": _detect_codecarbon_install_method(),
        "country_name": emissions.country_name,
        "country_iso_code": emissions.country_iso_code,
        "region": region,
        "cloud_provider": cloud_provider,
        "cloud_region": cloud_region,
        "on_cloud": on_cloud,
        "cpu_count": conf.get("cpu_count"),
        "cpu_physical_count": conf.get("cpu_physical_count"),
        "cpu_model": conf.get("cpu_model"),
        "cpu_architecture": platform.machine(),
        "gpu_count": conf.get("gpu_count"),
        "gpu_model": conf.get("gpu_model"),
        "ram_total_size_gb": conf.get("ram_total_size"),
        "tracking_mode": conf.get("tracking_mode"),
        "integration_surface": integration_surface,
        "offline_mode": integration_surface == "offline_tracker",
        "output_methods": _collect_output_methods(ctx),
        "save_to_api_enabled": ctx.save_to_api,
        "task_tracking_used": bool(ctx.tasks),
        "measure_power_interval_secs": ctx.measure_power_secs,
        "in_container": in_container,
        "container_runtime": container_runtime,
        "ci_environment": _first_env_match(CI_ENVIRONMENTS),
        "notebook_environment": _detect_notebook_environment(),
        "ide_used": _detect_ide(),
        "cudnn_version": _cudnn_version(),
        "duration_seconds": float(emissions.duration) if emissions.duration else None,
        "total_emissions_kg": emissions.emissions,
        "emissions_rate_kg_per_sec": emissions.emissions_rate,
        "energy_consumed_kwh": emissions.energy_consumed,
        "cpu_energy_kwh": emissions.cpu_energy,
        "gpu_energy_kwh": emissions.gpu_energy,
        "ram_energy_kwh": emissions.ram_energy,
        "cpu_utilization_avg": emissions.cpu_utilization_percent,
        "gpu_utilization_avg": emissions.gpu_utilization_percent,
        "ram_utilization_avg": emissions.ram_utilization_percent,
        "telemetry_level": level.value,
        **_collect_framework_fields(),
        **_collect_hardware_diagnostics(ctx),
        **gpu_fields,
    }

    payload = {key: raw[key] for key in PRIVATE_TELEMETRY_FIELDS if key in raw}
    return _strip_none(payload)
