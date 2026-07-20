"""Core enums for emission metric fields, HTTP header presets, and HTTP methods."""

from __future__ import annotations

from enum import Enum


class EmissionMetricField(str, Enum):
    """Measurable emission / energy fields suitable for labels and HTTP headers."""

    EMISSIONS = "emissions"
    EMISSIONS_RATE = "emissions_rate"
    DURATION = "duration"
    ENERGY_CONSUMED = "energy_consumed"
    CPU_ENERGY = "cpu_energy"
    GPU_ENERGY = "gpu_energy"
    RAM_ENERGY = "ram_energy"
    WATER_CONSUMED = "water_consumed"
    CPU_POWER = "cpu_power"
    GPU_POWER = "gpu_power"
    RAM_POWER = "ram_power"
    CPU_UTILIZATION_PERCENT = "cpu_utilization_percent"
    GPU_UTILIZATION_PERCENT = "gpu_utilization_percent"
    RAM_UTILIZATION_PERCENT = "ram_utilization_percent"
    RAM_USED_GB = "ram_used_gb"
    PUE = "pue"
    WUE = "wue"

    @property
    def unit(self) -> str:
        """Return the canonical unit suffix for this field."""
        return _FIELD_UNITS[self]


_FIELD_UNITS: dict[EmissionMetricField, str] = {
    EmissionMetricField.EMISSIONS: "kg",
    EmissionMetricField.EMISSIONS_RATE: "kg-per-s",
    EmissionMetricField.DURATION: "s",
    EmissionMetricField.ENERGY_CONSUMED: "kwh",
    EmissionMetricField.CPU_ENERGY: "kwh",
    EmissionMetricField.GPU_ENERGY: "kwh",
    EmissionMetricField.RAM_ENERGY: "kwh",
    EmissionMetricField.WATER_CONSUMED: "l",
    EmissionMetricField.CPU_POWER: "w",
    EmissionMetricField.GPU_POWER: "w",
    EmissionMetricField.RAM_POWER: "w",
    EmissionMetricField.CPU_UTILIZATION_PERCENT: "percent",
    EmissionMetricField.GPU_UTILIZATION_PERCENT: "percent",
    EmissionMetricField.RAM_UTILIZATION_PERCENT: "percent",
    EmissionMetricField.RAM_USED_GB: "gb",
    EmissionMetricField.PUE: "ratio",
    EmissionMetricField.WUE: "l-per-kwh",
}


def auto_header_name(field: EmissionMetricField | str) -> str:
    """Build an ``X-CodeCarbon-...`` header name from a field and its unit."""
    if isinstance(field, EmissionMetricField):
        field_name = field.value
        unit = field.unit
    else:
        field_name = field
        try:
            unit = EmissionMetricField(field).unit
        except ValueError:
            unit = ""
    title = "-".join(part.capitalize() for part in field_name.split("_"))
    suffix = f"-{unit}" if unit else ""
    return f"X-CodeCarbon-{title}{suffix}"


class HeaderPreset(str, Enum):
    """Named collections of emission fields for HTTP response headers."""

    EMISSIONS = "emissions"
    DEFAULT = "default"
    ENERGY = "energy"
    POWER = "power"
    FULL = "full"


_PRESET_FIELDS: dict[HeaderPreset, tuple[EmissionMetricField, ...]] = {
    HeaderPreset.EMISSIONS: (EmissionMetricField.EMISSIONS,),
    HeaderPreset.DEFAULT: (
        EmissionMetricField.EMISSIONS,
        EmissionMetricField.ENERGY_CONSUMED,
        EmissionMetricField.DURATION,
        EmissionMetricField.EMISSIONS_RATE,
    ),
    HeaderPreset.ENERGY: (
        EmissionMetricField.EMISSIONS,
        EmissionMetricField.ENERGY_CONSUMED,
        EmissionMetricField.CPU_ENERGY,
        EmissionMetricField.GPU_ENERGY,
        EmissionMetricField.RAM_ENERGY,
        EmissionMetricField.DURATION,
    ),
    HeaderPreset.POWER: (
        EmissionMetricField.EMISSIONS,
        EmissionMetricField.CPU_POWER,
        EmissionMetricField.GPU_POWER,
        EmissionMetricField.RAM_POWER,
        EmissionMetricField.DURATION,
    ),
    HeaderPreset.FULL: tuple(EmissionMetricField),
}


def preset_header_mapping(preset: HeaderPreset) -> dict[str, str]:
    """Return ``{field_name: header_name}`` for a preset."""
    return {field.value: auto_header_name(field) for field in _PRESET_FIELDS[preset]}


def field_units_dict() -> dict[str, str]:
    """Backward-compatible ``{field_name: unit}`` mapping."""
    return {field.value: field.unit for field in EmissionMetricField}


def header_presets_dict() -> dict[str, dict[str, str]]:
    """Backward-compatible preset name → field/header mapping (excludes ``full``)."""
    return {
        preset.value: preset_header_mapping(preset)
        for preset in HeaderPreset
        if preset is not HeaderPreset.FULL
    }


class HttpMethod(str, Enum):
    """Standard HTTP methods used for route include/exclude patterns."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    CONNECT = "CONNECT"
