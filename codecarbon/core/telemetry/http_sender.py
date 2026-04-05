"""HTTP payload helpers for telemetry (Tier 1 vs public emissions)."""

from typing import Any, Dict

from codecarbon.core.telemetry.collector import TelemetryData
from codecarbon.core.telemetry.config import TelemetryTier

_TIER1_EXCLUDE_KEYS: frozenset[str] = frozenset(
    {
        "total_emissions_kg",
        "emissions_rate_kg_per_sec",
        "energy_consumed_kwh",
        "cpu_energy_kwh",
        "gpu_energy_kwh",
        "ram_energy_kwh",
        "duration_seconds",
        "cpu_utilization_avg",
        "gpu_utilization_avg",
        "ram_utilization_avg",
    }
)

def tier1_telemetry_body(data: TelemetryData, tier: TelemetryTier) -> Dict[str, Any]:
    """Build POST /telemetry JSON body: Tier-1 fields only, plus telemetry_tier."""
    raw = data.to_dict()
    body = {k: v for k, v in raw.items() if k not in _TIER1_EXCLUDE_KEYS}
    body["telemetry_tier"] = tier.value
    return body


def public_emissions_body(
    total_emissions_kg: float = 0.0,
    emissions_rate_kg_per_sec: float = 0.0,
    energy_consumed_kwh: float = 0.0,
    cpu_energy_kwh: float = 0.0,
    gpu_energy_kwh: float = 0.0,
    ram_energy_kwh: float = 0.0,
    duration_seconds: float = 0.0,
    cpu_utilization_avg: float = 0.0,
    gpu_utilization_avg: float = 0.0,
    ram_utilization_avg: float = 0.0,
) -> Dict[str, Any]:
    """Build flat POST /emissions JSON body (public tier)."""
    return {
        "total_emissions_kg": total_emissions_kg,
        "emissions_rate_kg_per_sec": emissions_rate_kg_per_sec,
        "energy_consumed_kwh": energy_consumed_kwh,
        "cpu_energy_kwh": cpu_energy_kwh,
        "gpu_energy_kwh": gpu_energy_kwh,
        "ram_energy_kwh": ram_energy_kwh,
        "duration_seconds": duration_seconds,
        "cpu_utilization_avg": cpu_utilization_avg,
        "gpu_utilization_avg": gpu_utilization_avg,
        "ram_utilization_avg": ram_utilization_avg,
    }
