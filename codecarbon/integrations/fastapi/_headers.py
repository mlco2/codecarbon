"""Configurable response headers from emissions measurements."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Union

from starlette.requests import Request
from starlette.responses import Response

from codecarbon.core.emission_fields import (
    HeaderPreset,
    auto_header_name,
    field_units_dict,
    header_presets_dict,
    preset_header_mapping,
)
from codecarbon.output_methods.emissions_data import EmissionsData

HeaderConfig = Union[bool, str, Sequence[str], Mapping[str, str], None]
HeaderFormatter = Callable[[EmissionsData, Request], Mapping[str, str]]

FIELD_UNITS: dict[str, str] = field_units_dict()
HEADER_PRESETS: dict[str, dict[str, str]] = header_presets_dict()
FULL_HEADER_FIELDS: tuple[str, ...] = tuple(FIELD_UNITS.keys())


def _auto_header_name(field: str) -> str:
    return auto_header_name(field)


def _preset_mapping(preset: HeaderPreset) -> dict[str, str]:
    return preset_header_mapping(preset)


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
        ValueError: If ``config`` is a string that is not a known preset.
    """
    if not config:
        return {}

    match config:
        case True:
            return _preset_mapping(HeaderPreset.EMISSIONS)
        case str() as name:
            try:
                return _preset_mapping(HeaderPreset(name))
            except ValueError as exc:
                raise ValueError(f"Unknown response_headers preset: {name!r}") from exc
        case Mapping() as mapping:
            return dict(mapping)
        case Sequence() as fields:
            return {field: _auto_header_name(field) for field in fields}
        case _:
            return {}


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
        (name.encode("latin-1"), value.encode("latin-1"))
        for name, value in pairs.items()
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
    for name, value in header_name_value_pairs(emissions_data, header_mapping).items():
        response.headers[name] = value
