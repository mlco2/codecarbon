"""
Process-level cache for hardware detection and setup.

Reuses the outcome of the first tracker hardware probe so additional runs on
the same device (same process) skip repeated powermetrics, cpuinfo, and GPU
detection work.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from codecarbon.core.resource_tracker import ResourceTracker

CONF_KEYS = (
    "ram_total_size",
    "cpu_model",
    "gpu_count",
    "gpu_model",
    "gpu_ids",
)

_cache_lock = threading.Lock()
_plans: Dict["_HardwareCacheKey", "_HardwarePlan"] = {}
_tdp_model: Any = None


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


def make_key(tracker) -> _HardwareCacheKey:
    gpu_ids = tracker._gpu_ids
    if gpu_ids is not None:
        gpu_ids = tuple(gpu_ids)
    return _HardwareCacheKey(
        tracking_mode=tracker._tracking_mode,
        force_cpu_power=tracker._force_cpu_power,
        force_ram_power=tracker._force_ram_power,
        force_mode_cpu_load=bool(tracker._conf.get("force_mode_cpu_load", False)),
        gpu_ids=gpu_ids,
        rapl_include_dram=bool(tracker._rapl_include_dram),
        rapl_prefer_psys=bool(tracker._rapl_prefer_psys),
    )


def get_cached_tdp(cpu_module):
    """Return a shared cpu.TDP() instance for this process."""
    global _tdp_model
    if _tdp_model is None:
        _tdp_model = cpu_module.TDP()
    return _tdp_model


def _hardware_kind(hw) -> str:
    """Classify hardware without isinstance (safe if modules were reloaded)."""
    name = type(hw).__name__
    if name == "RAM":
        return "ram"
    if name == "CPU":
        return "cpu"
    if name == "AppleSiliconChip":
        return "apple_chip"
    if name == "GPU":
        return "gpu"
    raise TypeError(f"Unsupported hardware type for cache: {type(hw)}")


def _spec_from_hardware(hw) -> Dict[str, Any]:
    kind = _hardware_kind(hw)
    if kind == "ram":
        return {
            "kind": "ram",
            "tracking_mode": hw._tracking_mode,
            "force_ram_power": hw._force_ram_power,
        }
    if kind == "cpu":
        spec: Dict[str, Any] = {
            "kind": "cpu",
            "mode": hw._mode,
            "model": hw._model,
            "tdp": hw._tdp,
            "tracking_mode": hw._tracking_mode,
            "rapl_include_dram": False,
            "rapl_prefer_psys": False,
        }
        if hw._mode == "intel_rapl" and hasattr(hw, "_intel_interface"):
            spec["rapl_include_dram"] = getattr(
                hw._intel_interface, "rapl_include_dram", False
            )
            spec["rapl_prefer_psys"] = getattr(
                hw._intel_interface, "rapl_prefer_psys", False
            )
        return spec
    if kind == "apple_chip":
        return {
            "kind": "apple_chip",
            "model": hw._model,
            "chip_part": hw.chip_part,
        }
    if kind == "gpu":
        return {"kind": "gpu", "gpu_ids": list(hw.gpu_ids) if hw.gpu_ids else None}
    raise TypeError(f"Unsupported hardware type for cache: {type(hw)}")


def _hardware_from_spec(spec: Dict[str, Any], output_dir: str):
    from codecarbon.external.hardware import AppleSiliconChip, CPU, GPU
    from codecarbon.external.ram import RAM

    kind = spec["kind"]
    if kind == "ram":
        return RAM(
            tracking_mode=spec["tracking_mode"],
            force_ram_power=spec.get("force_ram_power"),
        )
    if kind == "cpu":
        return CPU(
            output_dir=output_dir,
            mode=spec["mode"],
            model=spec["model"],
            tdp=spec["tdp"],
            tracking_mode=spec["tracking_mode"],
            rapl_include_dram=spec.get("rapl_include_dram", False),
            rapl_prefer_psys=spec.get("rapl_prefer_psys", False),
        )
    if kind == "apple_chip":
        return AppleSiliconChip(
            output_dir=output_dir,
            model=spec["model"],
            chip_part=spec["chip_part"],
        )
    if kind == "gpu":
        return GPU.from_utils(gpu_ids=spec.get("gpu_ids"))
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
    tracker._hardware = [
        _hardware_from_spec(spec, tracker._output_dir) for spec in plan.hardware_specs
    ]


def get_or_run_setup(
    resource_tracker: "ResourceTracker", setup_fn,
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
    global _tdp_model
    with _cache_lock:
        _plans.clear()
    _tdp_model = None

    import sys

    gpu_nvidia = sys.modules.get("codecarbon.core.gpu_nvidia")
    if gpu_nvidia is not None:
        gpu_nvidia.clear_nvidia_system_cache()
    gpu_amd = sys.modules.get("codecarbon.core.gpu_amd")
    if gpu_amd is not None:
        gpu_amd.clear_rocm_system_cache()

    cpu = sys.modules.get("codecarbon.core.cpu")
    if cpu is not None:
        cpu.clear_powergadget_cache()
    powermetrics = sys.modules.get("codecarbon.core.powermetrics")
    if powermetrics is not None:
        powermetrics.clear_powermetrics_cache()

    if "codecarbon.external.hardware" in sys.modules:
        from codecarbon.external.hardware import clear_cpu_load_prime_cache

        clear_cpu_load_prime_cache()
