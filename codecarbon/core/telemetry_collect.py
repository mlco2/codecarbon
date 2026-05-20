"""Collect and project private product telemetry (Tier 1 / Tier 2) from tracker state."""

from __future__ import annotations

import importlib.util
import os
import platform
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from codecarbon.core.cloud import get_env_cloud_details
from codecarbon.core.gpu import is_nvidia_system
from codecarbon.core.telemetry_schemas import PRIVATE_TELEMETRY_FIELDS, TelemetryLevel
from codecarbon.output_methods.emissions_data import EmissionsData

FRAMEWORK_PACKAGES = (
    ("torch", "has_torch"),
    ("transformers", "has_transformers"),
    ("diffusers", "has_diffusers"),
    ("sklearn", "has_sklearn"),
)

def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if value == [] or value == {}:
        return False
    if isinstance(value, str) and value == "":
        return False
    return True


def _strip_none(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if _non_empty(value)}


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


def _detect_python_package_manager() -> Optional[str]:
    if os.environ.get("UV"):
        return "uv"
    if os.environ.get("POETRY_ACTIVE"):
        return "poetry"
    if os.environ.get("PIP_RUN"):
        return "pip"
    return None


def _detect_ci_environment() -> Optional[str]:
    if os.environ.get("GITHUB_ACTIONS"):
        return "github_actions"
    if os.environ.get("GITLAB_CI"):
        return "gitlab_ci"
    if os.environ.get("CIRCLECI"):
        return "circleci"
    if os.environ.get("JENKINS_URL"):
        return "jenkins"
    if os.environ.get("CI"):
        return "ci"
    return None


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


def _detect_in_container() -> bool:
    if os.path.exists("/.dockerenv"):
        return True
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        return True
    return False


def _detect_container_runtime() -> Optional[str]:
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        return "kubernetes"
    if os.path.exists("/.dockerenv"):
        return "docker"
    return None


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


def _collect_hardware_diagnostics(tracker: Any) -> dict[str, Any]:
    from codecarbon.core import cpu

    hardware_tracked: list[str] = []
    for item in getattr(tracker, "_hardware", []) or []:
        try:
            hardware_tracked.append(item.description())
        except Exception:
            pass

    resource_tracker = getattr(tracker, "_resource_tracker", None)
    gpu_detection_method: Optional[str] = None
    if resource_tracker is not None:
        gpu_tracker = getattr(resource_tracker, "gpu_tracker", None)
        if gpu_tracker and gpu_tracker != "Unspecified":
            gpu_detection_method = gpu_tracker

    rapl_available: Optional[bool] = None
    if platform.system() == "Linux":
        rapl_available = cpu.is_rapl_available()

    save_to_api = bool(getattr(tracker, "_save_to_api", False))
    return {
        "hardware_tracked": hardware_tracked or None,
        "hardware_detection_success": bool(hardware_tracked),
        "rapl_available": rapl_available,
        "gpu_detection_method": gpu_detection_method,
        "api_mode": "online" if save_to_api else "offline",
    }


def _detect_integration_surface(tracker: Any) -> str:
    from codecarbon.emissions_tracker import OfflineEmissionsTracker

    if isinstance(tracker, OfflineEmissionsTracker):
        return "offline_tracker"
    argv = " ".join(sys.argv)
    if "codecarbon" in argv and "monitor" in argv:
        return "cli_monitor"
    return "library"


def _collect_output_methods(tracker: Any) -> list[str]:
    methods: list[str] = []
    if getattr(tracker, "_save_to_file", False):
        methods.append("file")
    if getattr(tracker, "_save_to_api", False):
        methods.append("api")
    if getattr(tracker, "_save_to_logger", False):
        methods.append("logger")
    if getattr(tracker, "_emissions_endpoint", None):
        methods.append("http")
    if getattr(tracker, "_save_to_prometheus", False):
        methods.append("prometheus")
    if getattr(tracker, "_save_to_logfire", False):
        methods.append("logfire")
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


def collect_telemetry_context(
    tracker: Any,
    emissions: EmissionsData,
) -> dict[str, Any]:
    """Build a flat telemetry context from tracker state and emissions at stop.

    Args:
        tracker: Active ``BaseEmissionsTracker`` instance.
        emissions: Total emissions row from ``_prepare_emissions_data()``.

    Returns:
        Flat dictionary for ``project_private_telemetry``.
    """
    conf = getattr(tracker, "_conf", {})
    raw_provider, raw_region = _raw_cloud_provider_and_region()
    on_cloud = emissions.on_cloud == "Y"
    cloud_provider = emissions.cloud_provider or raw_provider
    cloud_region = emissions.cloud_region or raw_region
    region = emissions.region or conf.get("region")
    if on_cloud and cloud_region:
        region = region or cloud_region

    integration_surface = _detect_integration_surface(tracker)
    gpu_fields = _gpu_static_fields()

    context: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc),
        "os": conf.get("os") or platform.platform(),
        "python_version": conf.get("python_version") or platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_env_type": _detect_python_env_type(),
        "python_package_manager": _detect_python_package_manager(),
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
        "output_methods": _collect_output_methods(tracker),
        "save_to_api_enabled": bool(getattr(tracker, "_save_to_api", False)),
        "task_tracking_used": bool(getattr(tracker, "_tasks", {})),
        "measure_power_interval_secs": getattr(tracker, "_measure_power_secs", None),
        "in_container": _detect_in_container(),
        "container_runtime": _detect_container_runtime(),
        "ci_environment": _detect_ci_environment(),
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
        **_collect_framework_fields(),
        **_collect_hardware_diagnostics(tracker),
    }

    context.update(gpu_fields)
    return _strip_none(context)


def project_private_telemetry(
    context: dict[str, Any],
    level: TelemetryLevel = TelemetryLevel.minimal,
) -> dict[str, Any]:
    """Project context to private ``POST /telemetry`` fields for the resolved tier."""
    payload = {
        key: context[key]
        for key in PRIVATE_TELEMETRY_FIELDS
        if key in context
    }
    payload["telemetry_level"] = level.value
    return _strip_none(payload)


def build_telemetry_payload(
    tracker: Any,
    emissions: EmissionsData,
    level: TelemetryLevel = TelemetryLevel.minimal,
) -> dict[str, Any]:
    """Build a private telemetry payload dict for ``TelemetryCreate``.

    Args:
        tracker: Active emissions tracker.
        emissions: Run emissions data.
        level: Resolved ``TelemetryLevel`` (``minimal`` or ``extensive``).

    Returns:
        Payload dict for ``POST /telemetry``.
    """
    context = collect_telemetry_context(tracker, emissions)
    return project_private_telemetry(context, level=level)
