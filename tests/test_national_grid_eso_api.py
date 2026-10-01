import unittest

import pytest
import responses

from codecarbon.core import national_grid_eso_api
from codecarbon.core.national_grid_eso_api import NationalGridESOAPIError
from codecarbon.core.units import Energy
from codecarbon.external.geography import GeoMetadata


class TestNationalGridESOAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._energy = Energy.from_energy(kWh=10)
        self._geo = GeoMetadata(
            country_iso_code="GBR",
            country_name="United Kingdom",
            region=None,
            country_2letter_iso_code="GB",
        )

    # ------------------------------------------------------------------
    # is_supported
    # ------------------------------------------------------------------

    def test_is_supported_gbr(self):
        assert national_grid_eso_api.is_supported(self._geo) is True

    def test_is_supported_other_country(self):
        geo = GeoMetadata(
            country_iso_code="FRA",
            country_name="France",
            region=None,
            country_2letter_iso_code="FR",
        )
        assert national_grid_eso_api.is_supported(geo) is False

    # ------------------------------------------------------------------
    # get_emissions – happy paths
    # ------------------------------------------------------------------

    @responses.activate
    def test_get_emissions_uses_actual(self):
        responses.add(
            responses.GET,
            national_grid_eso_api.URL,
            json={"data": [{"intensity": {"forecast": 266, "actual": 263, "index": "moderate"}}]},
            status=200,
        )
        result = national_grid_eso_api.get_emissions(self._energy, self._geo)
        # 263 g/kWh * 0.001 kg/g * 10 kWh = 2.63 kg
        assert round(result, 5) == 2.63

    @responses.activate
    def test_get_emissions_uses_actual_zero(self):
        # actual=0 is a valid value and must not fall through to forecast
        responses.add(
            responses.GET,
            national_grid_eso_api.URL,
            json={"data": [{"intensity": {"forecast": 266, "actual": 0, "index": "very low"}}]},
            status=200,
        )
        result = national_grid_eso_api.get_emissions(self._energy, self._geo)
        # 0 g/kWh * 10 kWh = 0.0 kg
        assert result == 0.0

    @responses.activate
    def test_get_emissions_falls_back_to_forecast_when_actual_is_none(self):
        responses.add(
            responses.GET,
            national_grid_eso_api.URL,
            json={"data": [{"intensity": {"forecast": 266, "actual": None, "index": "moderate"}}]},
            status=200,
        )
        result = national_grid_eso_api.get_emissions(self._energy, self._geo)
        # 266 g/kWh * 0.001 * 10 kWh = 2.66 kg
        assert round(result, 5) == 2.66

    @responses.activate
    def test_get_emissions_falls_back_to_forecast_when_actual_absent(self):
        responses.add(
            responses.GET,
            national_grid_eso_api.URL,
            json={"data": [{"intensity": {"forecast": 200, "index": "low"}}]},
            status=200,
        )
        result = national_grid_eso_api.get_emissions(self._energy, self._geo)
        assert round(result, 5) == 2.0

    # ------------------------------------------------------------------
    # get_emissions – error paths
    # ------------------------------------------------------------------

    @responses.activate
    def test_get_emissions_raises_on_http_error(self):
        responses.add(
            responses.GET,
            national_grid_eso_api.URL,
            json={"error": "Service unavailable"},
            status=503,
        )
        with self.assertRaises(NationalGridESOAPIError):
            national_grid_eso_api.get_emissions(self._energy, self._geo)

    @responses.activate
    def test_get_emissions_raises_when_both_actual_and_forecast_are_none(self):
        responses.add(
            responses.GET,
            national_grid_eso_api.URL,
            json={"data": [{"intensity": {"forecast": None, "actual": None, "index": "unknown"}}]},
            status=200,
        )
        with self.assertRaises(NationalGridESOAPIError):
            national_grid_eso_api.get_emissions(self._energy, self._geo)

    @responses.activate
    def test_get_emissions_raises_on_malformed_response(self):
        responses.add(
            responses.GET,
            national_grid_eso_api.URL,
            json={"unexpected": "shape"},
            status=200,
        )
        with self.assertRaises(NationalGridESOAPIError):
            national_grid_eso_api.get_emissions(self._energy, self._geo)

    @pytest.mark.integ_test
    @unittest.skip("Skip real API call in regular test runs")
    def test_get_emissions_real_api(self):
        result = national_grid_eso_api.get_emissions(self._energy, self._geo)
        assert result > 0
