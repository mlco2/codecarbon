"""Configurable response headers from emissions measurements."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Union

from starlette.requests import Request
from starlette.responses import Response

from codecarbon.output_methods.emissions_data import EmissionsData

HeaderConfig = Union[bool, str, Sequence[str], Mapping[str, str], None]
HeaderFormatter = Callable[[EmissionsData, Request], Mapping[str, str]]

FIELD_UNITS: dict[str, str] = {
    "emissions": "kg",
    "emissions_rate": "kg-per-s",
    "duration": "s",
    "energy_consumed": "kwh",
    "cpu_energy": "kwh",
    "gpu_energy": "kwh",
    "ram_energy": "kwh",
    "water_consumed": "l",
    "cpu_power": "w",
    "gpu_power": "w",
    "ram_power": "w",
    "cpu_utilization_percent": "percent",
    "gpu_utilization_percent": "percent",
    "ram_utilization_percent": "percent",
    "ram_used_gb": "gb",
    "pue": "ratio",
    "wue": "l-per-kwh",
}

HEADER_PRESETS: dict[str, dict[str, str]] = {
    "emissions": {"emissions": "X-CodeCarbon-Emissions-kg"},
    "default": {
        "emissions": "X-CodeCarbon-Emissions-kg",
        "energy_consumed": "X-CodeCarbon-Energy-Consumed-kwh",
        "duration": "X-CodeCarbon-Duration-s",
        "emissions_rate": "X-CodeCarbon-Emissions-Rate-kg-per-s",
    },
    "energy": {
        "emissions": "X-CodeCarbon-Emissions-kg",
        "energy_consumed": "X-CodeCarbon-Energy-Consumed-kwh",
        "cpu_energy": "X-CodeCarbon-Cpu-Energy-kwh",
        "gpu_energy": "X-CodeCarbon-Gpu-Energy-kwh",
        "ram_energy": "X-CodeCarbon-Ram-Energy-kwh",
        "duration": "X-CodeCarbon-Duration-s",
    },
    "power": {
        "emissions": "X-CodeCarbon-Emissions-kg",
        "cpu_power": "X-CodeCarbon-Cpu-Power-w",
        "gpu_power": "X-CodeCarbon-Gpu-Power-w",
        "ram_power": "X-CodeCarbon-Ram-Power-w",
        "duration": "X-CodeCarbon-Duration-s",
    },
}

FULL_HEADER_FIELDS: tuple[str, ...] = tuple(FIELD_UNITS.keys())


def _auto_header_name(field: str) -> str:
    unit = FIELD_UNITS.get(field, "")
    title = "-".join(part.capitalize() for part in field.split("_"))
    suffix = f"-{unit}" if unit else ""
    return f"X-CodeCarbon-{title}{suffix}"


def resolve_header_mapping(config: HeaderConfig) -> dict[str, str]:
    """Normalize ``response_headers`` settings to ``{field_name: header_name}``.

    Args:
        config: ``None`` or ``False`` for no headers; ``True`` for the emissions preset;
            a preset name (``emissions``, ``default``, ``energy``, ``power``, ``full``);
            a sequence of field names (auto header names); or an explicit mapping.

    Returns:
        Mapping from :class:`~codecarbon.output_methods.emissions_data.EmissionsData`
        attribute names to HTTP header names.

    Raises:
        ValueError: If ``config`` is a string that is not a known preset (other than
            ``full``).
    """
    if config is None or config is False:
        return {}
    if config is True:
        return dict(HEADER_PRESETS["emissions"])
    if isinstance(config, str):
        preset = HEADER_PRESETS.get(config)
        if preset is None:
            if config == "full":
                return {field: _auto_header_name(field) for field in FULL_HEADER_FIELDS}
            raise ValueError(f"Unknown response_headers preset: {config!r}")
        return dict(preset)
    if isinstance(config, Mapping):
        return dict(config)
    return {field: _auto_header_name(field) for field in config}


def header_name_value_pairs(
    emissions_data: EmissionsData,
    header_mapping: Mapping[str, str],
    request: Request | None = None,
    header_formatter: HeaderFormatter | None = None,
) -> Mapping[str, str]:
    """Resolve emission fields to HTTP header names and string values."""
    if header_formatter is not None:
        if request is None:
            raise ValueError("request is required when header_formatter is set")
        return header_formatter(emissions_data, request)
    return {
        header_name: str(getattr(emissions_data, field))
        for field, header_name in header_mapping.items()
        if hasattr(emissions_data, field)
    }


def emissions_header_items(
    emissions_data: EmissionsData,
    header_mapping: Mapping[str, str],
    request: Request,
    header_formatter: HeaderFormatter | None = None,
) -> list[tuple[bytes, bytes]]:
    """Build ASGI header pairs for emission fields.

    Args:
        emissions_data: Measured values for this request.
        header_mapping: Field name to HTTP header name.
        request: Current HTTP request (for custom formatters).
        header_formatter: Optional override for header name/value pairs.

    Returns:
        List of ``(name, value)`` byte tuples for ASGI ``response.start`` messages.
    """
    pairs = header_name_value_pairs(
        emissions_data, header_mapping, request, header_formatter
    )
    return [
        (name.encode("latin-1"), value.encode("latin-1")) for name, value in pairs.items()
    ]


def apply_response_headers(
    response: Response,
    emissions_data: EmissionsData,
    header_mapping: Mapping[str, str],
) -> None:
    """Write selected emission fields onto an HTTP response as headers.

    Args:
        response: Outgoing Starlette response (headers are updated in place).
        emissions_data: Values read via ``getattr`` for each key in ``header_mapping``.
        header_mapping: Field name to HTTP header name; unknown fields are skipped.
    """
    for name, value in header_name_value_pairs(
        emissions_data, header_mapping
    ).items():
        response.headers[name] = value
