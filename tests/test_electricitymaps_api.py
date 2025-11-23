import unittest

import pytest
import responses

from codecarbon.core import electricitymaps_api
from codecarbon.core.units import Energy
from codecarbon.external.geography import GeoMetadata


class TestElectricityMapsAPI(unittest.TestCase):
    def setUp(self) -> None:
        # GIVEN
        self._energy = Energy.from_energy(kWh=10)
        self._geo = GeoMetadata(
            country_iso_code="FRA",
            country_name="France",
            region=None,
            country_2letter_iso_code="FR",
        )

    @responses.activate
    def test_get_emissions_RUNS(self):
        responses.add(
            responses.GET,
            electricitymaps_api.URL,
            json={
                "zone": "FR",
                "carbonIntensity": 58.765447504659946,
                "datetime": "2025-11-21T19:00:00.000Z",
                "updatedAt": "2025-11-21T19:09:54.950Z",
            },
            status=200,
        )
        result = electricitymaps_api.get_emissions(self._energy, self._geo)
        assert round(result, 5) == 0.58765

    @pytest.mark.integ_test
    @unittest.skip("Skip real API call in regular test runs")
    def test_get_emissions_with_api_key(self):
        """Test with real API call using provided API key"""
        api_key = "YOUR_REAL_API_KEY"
        result = electricitymaps_api.get_emissions(self._energy, self._geo, api_key)
        # Should return a positive emissions value
        assert result > 0
