import unittest
from unittest.mock import patch

import pytest

from codecarbon.core.carbon_intensity import (
    CarbonIntensityProvider,
    NationalGridESOProvider,
    build_providers,
)
from codecarbon.core.carbon_intensity.electricitymaps import (
    ElectricityMapsAPIError,
    ElectricityMapsProvider,
)
from codecarbon.core.emissions import Emissions
from codecarbon.core.units import Energy
from codecarbon.external.geography import GeoMetadata
from codecarbon.input import DataSource


class _FixedProvider(CarbonIntensityProvider):
    """A provider that returns a constant, counting its fetches."""

    name = "Fixed"
    cache_ttl = 60

    def __init__(self, value: float = 100.0):
        self.value = value
        self.fetches = 0

    @classmethod
    def from_config(cls, conf):
        return None

    def _cache_key(self, geo):
        return self.value

    def _fetch(self, geo):
        self.fetches += 1
        return self.value


class _FailingProvider(_FixedProvider):
    name = "Failing"

    def _fetch(self, geo):
        self.fetches += 1
        raise RuntimeError("API down")


GBR = GeoMetadata(country_iso_code="GBR", country_name="United Kingdom")


class TestBuildProviders(unittest.TestCase):
    def test_nothing_enabled_by_default(self):
        assert build_providers({}) == []

    def test_providers_are_built_in_priority_order(self):
        providers = build_providers(
            {"electricitymaps_api_token": "token", "use_national_grid_eso_api": True}
        )
        assert [type(p) for p in providers] == [
            ElectricityMapsProvider,
            NationalGridESOProvider,
        ]
        assert providers[0].api_token == "token"

    def test_each_provider_reads_only_its_own_keys(self):
        providers = build_providers({"use_national_grid_eso_api": True})
        assert [type(p) for p in providers] == [NationalGridESOProvider]


class TestCarbonIntensityProvider(unittest.TestCase):
    def setUp(self):
        _FixedProvider.reset_cache()
        _FailingProvider.reset_cache()

    def test_emissions_are_intensity_times_energy(self):
        provider = _FixedProvider(value=250.0)
        emissions = provider.get_emissions(Energy.from_energy(kWh=2), GBR)
        assert emissions == pytest.approx(0.5)

    def test_value_is_cached(self):
        provider = _FixedProvider()
        for _ in range(5):
            provider.get_carbon_intensity(GBR)
        assert provider.fetches == 1

    def test_state_is_not_shared_between_provider_classes(self):
        # GIVEN one provider class is in cooldown after a failure
        failing = _FailingProvider()
        with pytest.raises(RuntimeError):
            failing.get_carbon_intensity(GBR)

        # THEN another class with the same cache key is unaffected
        assert _FixedProvider().get_carbon_intensity(GBR) == 100.0
        assert _FixedProvider._states is not _FailingProvider._states


class TestEmissionsProviderChain(unittest.TestCase):
    def setUp(self):
        self._data_source = DataSource()
        _FixedProvider.reset_cache()
        _FailingProvider.reset_cache()

    def test_custom_providers_are_used(self):
        emissions = Emissions(self._data_source, providers=[_FixedProvider(400.0)])
        result = emissions.get_private_infra_emissions(Energy.from_energy(kWh=1), GBR)
        assert result == pytest.approx(0.4)

    def test_failing_provider_falls_through_to_the_next(self):
        failing, fixed = _FailingProvider(), _FixedProvider(300.0)
        emissions = Emissions(self._data_source, providers=[failing, fixed])

        result = emissions.get_private_infra_emissions(Energy.from_energy(kWh=1), GBR)

        assert result == pytest.approx(0.3)
        assert failing.fetches == 1

    @patch.object(NationalGridESOProvider, "get_emissions", return_value=0.2)
    @patch.object(
        ElectricityMapsProvider,
        "get_emissions",
        side_effect=ElectricityMapsAPIError("invalid token"),
    )
    def test_electricitymaps_failure_falls_back_to_national_grid_eso(
        self, mocked_em, mocked_eso
    ):
        emissions = Emissions(
            self._data_source,
            providers=build_providers(
                {
                    "electricitymaps_api_token": "bad-token",
                    "use_national_grid_eso_api": True,
                }
            ),
        )

        result = emissions.get_private_infra_emissions(Energy.from_energy(kWh=1), GBR)

        assert result == 0.2
        mocked_em.assert_called_once()
        mocked_eso.assert_called_once()

    def test_unsupported_location_skips_the_provider(self):
        emissions = Emissions(self._data_source, providers=[NationalGridESOProvider()])
        france = GeoMetadata(country_iso_code="FRA", country_name="France")
        with patch.object(NationalGridESOProvider, "_fetch") as mocked_fetch:
            emissions.get_private_infra_emissions(Energy.from_energy(kWh=1), france)
        mocked_fetch.assert_not_called()


class TestLegacyModules(unittest.TestCase):
    """The pre-package module paths keep working for existing imports."""

    def setUp(self):
        ElectricityMapsProvider.reset_cache()
        NationalGridESOProvider.reset_cache()

    def test_electricitymaps_api_delegates_to_the_provider(self):
        from codecarbon.core import electricitymaps_api

        assert electricitymaps_api.ElectricityMapsProvider is ElectricityMapsProvider
        with patch.object(ElectricityMapsProvider, "_fetch", return_value=200.0):
            result = electricitymaps_api.get_emissions(
                Energy.from_energy(kWh=1), GBR, "token"
            )
        assert result == pytest.approx(0.2)

    def test_national_grid_eso_api_delegates_to_the_provider(self):
        from codecarbon.core import national_grid_eso_api

        assert national_grid_eso_api.is_supported(GBR)
        with patch.object(NationalGridESOProvider, "_fetch", return_value=100.0):
            result = national_grid_eso_api.get_emissions(Energy.from_energy(kWh=1), GBR)
        assert result == pytest.approx(0.1)
