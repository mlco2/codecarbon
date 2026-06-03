"""Tests for response header mapping from :class:`~codecarbon.output_methods.emissions_data.EmissionsData`."""

import pytest
from starlette.responses import Response

from codecarbon.integrations.fastapi._headers import (
    HEADER_PRESETS,
    apply_response_headers,
    resolve_header_mapping,
)
from codecarbon.output_methods.emissions_data import EmissionsData


@pytest.fixture
def emissions_data() -> EmissionsData:
    return EmissionsData(
        timestamp="2026-05-19T12:00:00",
        project_name="test",
        run_id="run-1",
        experiment_id="exp-1",
        duration=1.5,
        emissions=0.00042,
        emissions_rate=0.00028,
        cpu_power=12.0,
        gpu_power=0.0,
        ram_power=5.0,
        cpu_energy=0.003,
        gpu_energy=0.0,
        ram_energy=0.001,
        energy_consumed=0.004,
        water_consumed=0.0,
        country_name="France",
        country_iso_code="FRA",
        region="",
        cloud_provider="",
        cloud_region="",
        os="Darwin",
        python_version="3.12",
        codecarbon_version="3.2.6",
        cpu_count=8,
        cpu_model="Apple M1",
        gpu_count=0,
        gpu_model="",
        longitude=2.35,
        latitude=48.85,
        ram_total_size=16.0,
        tracking_mode="machine",
    )


def test_resolve_header_mapping_preset_emissions() -> None:
    mapping = resolve_header_mapping("emissions")
    assert mapping == {"emissions": "X-CodeCarbon-Emissions-kg"}


def test_resolve_header_mapping_field_list() -> None:
    mapping = resolve_header_mapping(["emissions", "duration"])
    assert mapping["emissions"] == "X-CodeCarbon-Emissions-kg"
    assert mapping["duration"] == "X-CodeCarbon-Duration-s"


def test_resolve_header_mapping_custom_dict() -> None:
    custom = {"emissions": "X-App-CO2", "duration": "X-App-Time"}
    assert resolve_header_mapping(custom) == custom


def test_resolve_header_mapping_bool_true_aliases_emissions() -> None:
    assert resolve_header_mapping(True) == HEADER_PRESETS["emissions"]


def test_resolve_header_mapping_none_or_false_returns_empty() -> None:
    assert resolve_header_mapping(None) == {}
    assert resolve_header_mapping(False) == {}


def test_resolve_header_mapping_full_preset() -> None:
    mapping = resolve_header_mapping("full")
    assert mapping["emissions"] == "X-CodeCarbon-Emissions-kg"
    assert (
        mapping["cpu_utilization_percent"]
        == "X-CodeCarbon-Cpu-Utilization-Percent-percent"
    )


def test_resolve_header_mapping_unknown_preset_raises() -> None:
    with pytest.raises(ValueError, match="Unknown response_headers preset"):
        resolve_header_mapping("not-a-preset")


def test_apply_response_headers_sets_values(emissions_data: EmissionsData) -> None:
    response = Response(content=b"ok")
    apply_response_headers(
        response,
        emissions_data,
        {
            "emissions": "X-CodeCarbon-Emissions-kg",
            "duration": "X-CodeCarbon-Duration-s",
        },
    )
    assert response.headers["X-CodeCarbon-Emissions-kg"] == "0.00042"
    assert response.headers["X-CodeCarbon-Duration-s"] == "1.5"


def test_apply_response_headers_ignores_unknown_fields(
    emissions_data: EmissionsData,
) -> None:
    response = Response(content=b"ok")
    apply_response_headers(response, emissions_data, {"not_a_field": "X-Bad"})
    assert "X-Bad" not in response.headers


def test_apply_response_headers_noop_when_mapping_empty(
    emissions_data: EmissionsData,
) -> None:
    response = Response(content=b"ok")
    before = dict(response.headers)
    apply_response_headers(response, emissions_data, {})
    assert dict(response.headers) == before
