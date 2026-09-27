"""Collect private product telemetry from tracker state."""

from __future__ import annotations

import importlib.util
import os
import platform
import sys
from datetime import datetime, timezone
from typing import Any

from codecarbon.core.gpu import is_nvidia_system
from codecarbon.core.telemetry.schemas import TelemetryLevel
from codecarbon.output_methods.emissions_data import EmissionsData


def _strip_empty(data: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in data.items() if value not in (None, "", [], {})
    }


def _package_installed(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _cloud_region(
    emissions: EmissionsData,
) -> tuple[str | None, str | None, str | None]:
    # Reuse what the tracker already detected: probing the cloud metadata
    # endpoints again costs up to a few seconds off-cloud.
    cloud_provider = emissions.cloud_provider or None
    cloud_region = emissions.cloud_region or None
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


def _minimal_payload(
    tracker: Any, emissions: EmissionsData, level: TelemetryLevel
) -> dict[str, Any]:
    """Every field of ``TelemetryCreate``; empty values are dropped."""
    conf = getattr(tracker, "_conf", {})
    cloud_provider, cloud_region, region = _cloud_region(emissions)
    region = region or conf.get("region")

    payload = {
        # Truncated to the hour: enough to see usage trends over time without
        # pinning a row to the exact second a process ran.
        "timestamp": datetime.now(timezone.utc).replace(
            minute=0, second=0, microsecond=0
        ),
        "telemetry_level": level.value,
        "os": conf.get("os") or platform.platform(),
        "country_name": emissions.country_name,
        "country_iso_code": emissions.country_iso_code,
        "region": region,
        "cloud_provider": cloud_provider,
        "cloud_region": cloud_region,
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


def build_payload(
    tracker: Any,
    emissions: EmissionsData,
    level: TelemetryLevel = TelemetryLevel.minimal,
) -> dict[str, Any]:
    """Build a validated telemetry payload dict for ``POST /telemetry``."""
    return _minimal_payload(tracker, emissions, level)
