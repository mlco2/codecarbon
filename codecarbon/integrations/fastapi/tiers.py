"""Measurement capability tiers for per-request energy reporting.

A backend can only report a per-request energy figure if it actually resolves
the request. Measured on real hardware:

* ``intel_rapl``: counter updates ~1 ms, quantum 15.3 uJ, read cost ~10 us.
  A 30 ms request is genuinely resolved -> MEASURED.
* ``constant`` (TDP): ``power = tdp * 0.5``, so energy is analytic in duration
  and exact at any resolution, but it only restates wall time -> ESTIMATED.
* ``cpu_load``: ``psutil.cpu_percent(interval=None)`` is tick-quantized; 98% of
  5 ms reads return zero load and the ``0.1 + 0.9*(load/100)**3`` factor turns
  that into a 10%-of-TDP floor (30 requests on a pegged core all reported
  exactly 0.0900 J) -> AGGREGATE_ONLY.
* ``apple_powermetrics``: ``get_details()`` spawns ``sudo powermetrics -n 10
  -i 100`` and blocks ~1 s -> cannot run in a request path -> AGGREGATE_ONLY.
* NVML: sensor period 20 ms (V100) to ~100 ms with a 25 ms averaging window
  (A100/H100); sub-100 ms GPU energy is not obtainable. Only usable when
  aggregating over >= 1 s.
* ``amdsmi``, ``windows_emi``: update rate undocumented. Treated as unprobed
  -> AGGREGATE_ONLY.

Idle/baseline power is charged to requests, not subtracted, so per-endpoint
totals still sum to the run total.
"""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any, Iterable

from codecarbon.output_methods.emissions_data import EmissionsData


class MeasurementTier(str, Enum):
    """What the detected hardware can honestly report per request."""

    MEASURED = "measured"
    ESTIMATED = "estimated"
    AGGREGATE_ONLY = "aggregate_only"


_RANK = {
    MeasurementTier.AGGREGATE_ONLY: 0,
    MeasurementTier.ESTIMATED: 1,
    MeasurementTier.MEASURED: 2,
}

#: NVML only resolves energy when aggregated over at least this window.
NVML_MIN_AGGREGATION_SECONDS = 1.0

CPU_MODE_TIERS: dict[str, MeasurementTier] = {
    "intel_rapl": MeasurementTier.MEASURED,
    "constant": MeasurementTier.ESTIMATED,
    "cpu_load": MeasurementTier.AGGREGATE_ONLY,
    "apple_powermetrics": MeasurementTier.AGGREGATE_ONLY,
    "intel_power_gadget": MeasurementTier.AGGREGATE_ONLY,
    "windows_emi": MeasurementTier.AGGREGATE_ONLY,  # unprobed update rate
}


def hardware_tier(hardware: Any, window_seconds: float = 0.0) -> MeasurementTier:
    """Tier a single hardware component can support over ``window_seconds``.

    Duck-typed on purpose: tests inject stubs instead of depending on what the
    test machine happens to have.
    """
    mode = getattr(hardware, "_mode", None)
    if isinstance(mode, str):
        return CPU_MODE_TIERS.get(mode, MeasurementTier.AGGREGATE_ONLY)

    name = type(hardware).__name__
    if name == "GPU" or hasattr(hardware, "devices"):
        return _gpu_tier(hardware, window_seconds)
    if getattr(hardware, "analytic_power_model", False):
        return MeasurementTier.ESTIMATED
    if name == "AppleSiliconChip":
        return MeasurementTier.AGGREGATE_ONLY
    return MeasurementTier.AGGREGATE_ONLY


def _gpu_tier(hardware: Any, window_seconds: float) -> MeasurementTier:
    devices = getattr(getattr(hardware, "devices", None), "devices", None)
    if not devices:
        return MeasurementTier.AGGREGATE_ONLY
    if not all("Nvidia" in type(device).__name__ for device in devices):
        return MeasurementTier.AGGREGATE_ONLY  # amdsmi: unprobed
    if window_seconds >= NVML_MIN_AGGREGATION_SECONDS:
        return MeasurementTier.MEASURED
    return MeasurementTier.AGGREGATE_ONLY


@dataclasses.dataclass(frozen=True)
class TierDetection:
    """Resolved tier plus the per-component tiers it was derived from."""

    tier: MeasurementTier
    components: tuple[tuple[str, MeasurementTier], ...] = ()

    def describe(self) -> str:
        parts = ", ".join(f"{name}={tier.value}" for name, tier in self.components)
        return f"{self.tier.value} ({parts})" if parts else self.tier.value


def detect_measurement_tier(
    hardware: Iterable[Any] | None, window_seconds: float = 0.0
) -> TierDetection:
    """Resolve the reporting tier from the hardware a tracker detected.

    The overall tier is the weakest component tier: a run is only MEASURED if
    every energy contributor resolves the window.
    """
    try:
        detected = tuple(
            (hw, repr_hardware(hw), hardware_tier(hw, window_seconds))
            for hw in (hardware or ())
        )
    except TypeError:  # not iterable (e.g. a bare mock)
        detected = ()
    if not detected:
        return TierDetection(MeasurementTier.AGGREGATE_ONLY)
    components = tuple((name, tier) for _, name, tier in detected)
    # An analytic (constant-power) component is exact at any resolution, so it
    # never limits resolution: it is reported but does not vote.
    voting = [
        tier
        for hw, _, tier in detected
        if not getattr(hw, "analytic_power_model", False)
    ]
    if not voting:
        voting = [tier for _, tier in components]
    tier = min(voting, key=_RANK.__getitem__)
    return TierDetection(tier, components)


def repr_hardware(hardware: Any) -> str:
    mode = getattr(hardware, "_mode", None)
    name = type(hardware).__name__
    return f"{name}[{mode}]" if isinstance(mode, str) else name


@dataclasses.dataclass(frozen=True)
class RequestMeasurement:
    """Per-request result handed to consumers.

    ``emissions_data`` is ``None`` whenever a per-request energy figure would be
    a fabrication: the AGGREGATE_ONLY tier, or a request that spanned no
    completed sampling window. Zero is never reported in place of unknown.
    """

    tier: MeasurementTier
    task_name: str
    endpoint: str
    duration: float
    emissions_data: EmissionsData | None = None
    unavailable_reason: str | None = None

    @property
    def available(self) -> bool:
        return self.emissions_data is not None

    @property
    def emissions(self) -> float | None:
        return None if self.emissions_data is None else self.emissions_data.emissions

    @property
    def energy_consumed(self) -> float | None:
        if self.emissions_data is None:
            return None
        return self.emissions_data.energy_consumed


@dataclasses.dataclass
class EndpointTotals:
    """Aggregate per endpoint. Valid in every tier, including AGGREGATE_ONLY."""

    endpoint: str
    tier: MeasurementTier
    count: int = 0
    duration: float = 0.0
    energy_consumed: float = 0.0
    emissions: float = 0.0

    def add(self, emissions_data: EmissionsData | None) -> None:
        self.count += 1
        if emissions_data is None:
            return
        self.duration += emissions_data.duration or 0.0
        self.energy_consumed += emissions_data.energy_consumed or 0.0
        self.emissions += emissions_data.emissions or 0.0
