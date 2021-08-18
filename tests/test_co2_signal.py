import unittest

import pytest
import requests
import responses

from codecarbon.core import co2_signal
from codecarbon.core.units import Energy
from codecarbon.external.geography import GeoMetadata


class TestCO2Signal(unittest.TestCase):
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
            co2_signal.URL,
            json={
                "status": "ok",
                "countryCode": "FR",
                "data": {
                    "carbonIntensity": 58.765447504659946,
                    "fossilFuelPercentage": 8.464454194205029,
                },
                "units": {"carbonIntensity": "gCO2eq/kWh"},
            },
            status=200,
        )
        result = co2_signal.get_emissions(self._energy, self._geo)
        assert round(result, 5) == 0.58765

    @pytest.mark.integ_test
    def test_get_emissions_TIMEOUT(self):
        with self.assertRaises(
            (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout)
        ):
            co2_signal.get_emissions(self._energy, self._geo)
