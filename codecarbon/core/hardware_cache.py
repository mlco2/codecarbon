"""
Process-level cache for hardware detection and setup.

Reuses the outcome of the first tracker hardware probe so additional runs on
the same device (same process) skip repeated powermetrics, cpuinfo, and GPU
detection work.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from codecarbon.core.config import normalize_gpu_ids

if TYPE_CHECKING:
    from codecarbon.core.resource_tracker import ResourceTracker

DEFAULT_RAPL_DIR = "/sys/class/powercap/intel-rapl/subsystem"

CONF_KEYS = (
    "ram_total_size",
    "cpu_count",
    "cpu_physical_count",
    "cpu_model",
    "gpu_count",
    "gpu_model",
    "gpu_ids",
)


class HardwareKind(str, Enum):
    RAM = "ram"
    CPU = "cpu"
    APPLE_CHIP = "apple_chip"
    GPU = "gpu"


_cache_lock = threading.Lock()
_plans: Dict["_HardwareCacheKey", "_HardwarePlan"] = {}
_tdp = None


@dataclass(frozen=True)
class _HardwareCacheKey:
    tracking_mode: str
    force_cpu_power: Any
    force_ram_power: Any
    force_mode_cpu_load: bool
    gpu_ids: Any
    rapl_include_dram: bool
    rapl_prefer_psys: bool


@dataclass
class _HardwarePlan:
    ram_tracker: str
    cpu_tracker: str
    gpu_tracker: str
    conf: Dict[str, Any] = field(default_factory=dict)
    hardware_specs: List[Dict[str, Any]] = field(default_factory=list)


def _canonical_gpu_ids(
    gpu_ids: Optional[List],
) -> Optional[Tuple[str, ...]]:
    """Normalize GPU ids to a stable cache-key form (tuple of strings)."""
    if gpu_ids is None:
        return None
    if not isinstance(gpu_ids, (list, tuple)):
        gpu_ids = [gpu_ids]
    normalized = normalize_gpu_ids(list(gpu_ids))
    if not normalized:
        return None
    return tuple(str(gpu_id) for gpu_id in normalized)


def make_key(tracker) -> _HardwareCacheKey:
    return _HardwareCacheKey(
        tracking_mode=tracker._tracking_mode,
        force_cpu_power=tracker._force_cpu_power,
        force_ram_power=tracker._force_ram_power,
        force_mode_cpu_load=bool(tracker._conf.get("force_mode_cpu_load", False)),
        gpu_ids=_canonical_gpu_ids(tracker._gpu_ids),
        rapl_include_dram=bool(tracker._rapl_include_dram),
        rapl_prefer_psys=bool(tracker._rapl_prefer_psys),
    )


def get_cached_tdp(cpu_module):
    """Return a shared cpu.TDP() instance for this process."""
    global _tdp
    if _tdp is None:
        _tdp = cpu_module.TDP()
    return _tdp


def _hardware_kind(hw) -> HardwareKind:
    """Classify hardware without isinstance (safe if modules were reloaded)."""
    name = type(hw).__name__
    if name == "RAM":
        return HardwareKind.RAM
    if name == "CPU":
        return HardwareKind.CPU
    if name == "AppleSiliconChip":
        return HardwareKind.APPLE_CHIP
    if name == "GPU":
        return HardwareKind.GPU
    raise TypeError(f"Unsupported hardware type for cache: {type(hw)}")


def _spec_from_hardware(hw) -> Dict[str, Any]:
    kind = _hardware_kind(hw)
    if kind == HardwareKind.RAM:
        return {
            "kind": kind.value,
            "tracking_mode": hw._tracking_mode,
            "force_ram_power": hw._force_ram_power,
        }
    if kind == HardwareKind.CPU:
        spec: Dict[str, Any] = {
            "kind": kind.value,
            "mode": hw._mode,
            "model": hw._model,
            "tdp": hw._tdp,
            "tracking_mode": hw._tracking_mode,
            "rapl_include_dram": False,
            "rapl_prefer_psys": False,
        }
        if hw._mode == "intel_rapl" and hasattr(hw, "_intel_interface"):
            intel = hw._intel_interface
            spec["rapl_include_dram"] = getattr(intel, "rapl_include_dram", False)
            spec["rapl_prefer_psys"] = getattr(intel, "rapl_prefer_psys", False)
            spec["rapl_dir"] = getattr(intel, "_lin_rapl_dir", DEFAULT_RAPL_DIR)
        return spec
    if kind == HardwareKind.APPLE_CHIP:
        return {
            "kind": kind.value,
            "model": hw._model,
            "chip_part": hw.chip_part,
        }
    if kind == HardwareKind.GPU:
        gpu_ids = _canonical_gpu_ids(hw.gpu_ids)
        return {"kind": kind.value, "gpu_ids": list(gpu_ids) if gpu_ids else None}
    raise TypeError(f"Unsupported hardware type for cache: {type(hw)}")


def _hardware_from_spec(spec: Dict[str, Any], output_dir: str):
    from codecarbon.external.hardware import CPU, GPU, AppleSiliconChip
    from codecarbon.external.ram import RAM

    try:
        kind = HardwareKind(spec["kind"])
    except ValueError as exc:
        raise ValueError(f"Unknown hardware spec kind: {spec['kind']}") from exc

    if kind == HardwareKind.RAM:
        return RAM(
            tracking_mode=spec["tracking_mode"],
            force_ram_power=spec.get("force_ram_power"),
        )
    if kind == HardwareKind.CPU:
        return CPU(
            output_dir=output_dir,
            mode=spec["mode"],
            model=spec["model"],
            tdp=spec["tdp"],
            tracking_mode=spec["tracking_mode"],
            rapl_dir=spec.get("rapl_dir", DEFAULT_RAPL_DIR),
            rapl_include_dram=spec.get("rapl_include_dram", False),
            rapl_prefer_psys=spec.get("rapl_prefer_psys", False),
        )
    if kind == HardwareKind.APPLE_CHIP:
        return AppleSiliconChip(
            output_dir=output_dir,
            model=spec["model"],
            chip_part=spec["chip_part"],
        )
    if kind == HardwareKind.GPU:
        gpu_ids = _canonical_gpu_ids(spec.get("gpu_ids"))
        return GPU.from_utils(gpu_ids=list(gpu_ids) if gpu_ids else None)
    raise ValueError(f"Unknown hardware spec kind: {kind}")


def capture(resource_tracker: "ResourceTracker") -> _HardwarePlan:
    tracker = resource_tracker.tracker
    conf = {k: tracker._conf[k] for k in CONF_KEYS if k in tracker._conf}
    return _HardwarePlan(
        ram_tracker=resource_tracker.ram_tracker,
        cpu_tracker=resource_tracker.cpu_tracker,
        gpu_tracker=resource_tracker.gpu_tracker,
        conf=conf,
        hardware_specs=[_spec_from_hardware(hw) for hw in tracker._hardware],
    )


def apply(resource_tracker: "ResourceTracker", plan: _HardwarePlan) -> None:
    tracker = resource_tracker.tracker
    resource_tracker.ram_tracker = plan.ram_tracker
    resource_tracker.cpu_tracker = plan.cpu_tracker
    resource_tracker.gpu_tracker = plan.gpu_tracker
    tracker._conf.update(plan.conf)
    if "gpu_ids" in plan.conf:
        tracker._gpu_ids = plan.conf["gpu_ids"]
    tracker._hardware = [
        _hardware_from_spec(spec, tracker._output_dir) for spec in plan.hardware_specs
    ]


def get_or_run_setup(
    resource_tracker: "ResourceTracker",
    setup_fn,
) -> None:
    """Apply cached hardware plan or run full setup once per cache key."""
    key = make_key(resource_tracker.tracker)
    with _cache_lock:
        plan = _plans.get(key)
        if plan is not None:
            apply(resource_tracker, plan)
            return
        setup_fn()
        _plans[key] = capture(resource_tracker)


def clear_cache() -> None:
    """Clear cached plans (for tests)."""
    global _tdp
    import sys

    with _cache_lock:
        _plans.clear()
    _tdp = None

    for mod_name, clear_fn in (
        ("codecarbon.core.gpu_nvidia", "clear_nvidia_system_cache"),
        ("codecarbon.core.gpu_amd", "clear_rocm_system_cache"),
        ("codecarbon.core.cpu", "clear_powergadget_cache"),
        ("codecarbon.core.powermetrics", "clear_powermetrics_cache"),
        ("codecarbon.core.windows_emi", "clear_emi_cache"),
    ):
        mod = sys.modules.get(mod_name)
        if mod is not None:
            getattr(mod, clear_fn)()

    if "codecarbon.external.hardware" in sys.modules:
        from codecarbon.external.hardware import clear_cpu_load_prime_cache

        clear_cpu_load_prime_cache()
