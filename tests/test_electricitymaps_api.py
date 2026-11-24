import unittest

import pytest
import responses

from codecarbon.core.carbon_intensity import electricitymaps
from codecarbon.core.carbon_intensity.electricitymaps import ElectricityMapsProvider
from codecarbon.core.units import Energy
from codecarbon.external.geography import GeoMetadata


class TestElectricityMapsAPI(unittest.TestCase):
    def setUp(self) -> None:
        # GIVEN
        ElectricityMapsProvider.reset_cache()
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
            electricitymaps.URL,
            json={
                "zone": "FR",
                "carbonIntensity": 58.765447504659946,
                "datetime": "2025-11-21T19:00:00.000Z",
                "updatedAt": "2025-11-21T19:09:54.950Z",
            },
            status=200,
        )
        result = ElectricityMapsProvider().get_emissions(self._energy, self._geo)
        assert round(result, 5) == 0.58765

    @responses.activate
    def test_non_json_error_body_falls_back_to_text(self):
        responses.add(
            responses.GET,
            electricitymaps.URL,
            body="<html>502 Bad Gateway</html>",
            status=502,
        )
        with pytest.raises(electricitymaps.ElectricityMapsAPIError) as error:
            ElectricityMapsProvider().get_carbon_intensity(self._geo)
        assert "502 Bad Gateway" in str(error.value)
