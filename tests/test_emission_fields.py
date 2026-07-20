"""Tests for core emission field and HTTP method enums."""

from codecarbon.core.emission_fields import (
    EmissionMetricField,
    HeaderPreset,
    HttpMethod,
    auto_header_name,
    field_units_dict,
    header_presets_dict,
    preset_header_mapping,
)
from codecarbon.output_methods.emissions_data import EmissionsData


def test_emission_metric_field_units_cover_all_members() -> None:
    for field in EmissionMetricField:
        assert isinstance(field.unit, str)
        assert field.unit


def test_emission_metric_fields_exist_on_emissions_data() -> None:
    for field in EmissionMetricField:
        assert hasattr(EmissionsData, field.value) or field.value in {
            f.name for f in EmissionsData.__dataclass_fields__.values()
        }
        assert field.value in EmissionsData.__dataclass_fields__


def test_auto_header_name_uses_unit() -> None:
    assert (
        auto_header_name(EmissionMetricField.EMISSIONS) == "X-CodeCarbon-Emissions-kg"
    )
    assert auto_header_name("duration") == "X-CodeCarbon-Duration-s"


def test_header_preset_mappings() -> None:
    emissions = preset_header_mapping(HeaderPreset.EMISSIONS)
    assert emissions == {"emissions": "X-CodeCarbon-Emissions-kg"}

    full = preset_header_mapping(HeaderPreset.FULL)
    assert set(full) == {field.value for field in EmissionMetricField}


def test_backward_compat_dicts() -> None:
    units = field_units_dict()
    assert units["emissions"] == "kg"
    assert set(units) == {field.value for field in EmissionMetricField}

    presets = header_presets_dict()
    assert "emissions" in presets
    assert "full" not in presets
    assert presets["emissions"]["emissions"] == "X-CodeCarbon-Emissions-kg"


def test_http_method_values() -> None:
    assert HttpMethod.GET.value == "GET"
    assert "POST" in {m.value for m in HttpMethod}
    assert len(HttpMethod) == 9
