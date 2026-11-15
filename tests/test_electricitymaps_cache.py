import unittest
from unittest import mock

import responses

from codecarbon.core.carbon_intensity import electricitymaps
from codecarbon.core.carbon_intensity.electricitymaps import ElectricityMapsProvider
from codecarbon.core.emissions import Emissions
from codecarbon.core.units import Energy
from codecarbon.external.geography import GeoMetadata
from codecarbon.input import DataSource


class TestElectricityMapsCache(unittest.TestCase):
    def setUp(self) -> None:
        # GIVEN
        ElectricityMapsProvider.reset_cache()
        self._geo = GeoMetadata(
            country_iso_code="FRA",
            country_name="France",
            region=None,
            country_2letter_iso_code="FR",
        )
        self._other_geo = GeoMetadata(
            country_iso_code="DEU",
            country_name="Germany",
            region=None,
            country_2letter_iso_code="DE",
        )

    def tearDown(self) -> None:
        ElectricityMapsProvider.reset_cache()

    @staticmethod
    def _only_state():
        """The cache/cooldown state of the single key these tests use, if any."""
        return next(iter(ElectricityMapsProvider._states.values()), None)

    def _add_success_response(self, carbon_intensity: float = 58.7) -> None:
        responses.add(
            responses.GET,
            electricitymaps.URL,
            json={"zone": "FR", "carbonIntensity": carbon_intensity},
            status=200,
        )

    @responses.activate
    def test_second_call_within_ttl_does_not_hit_the_api(self):
        self._add_success_response()

        first = ElectricityMapsProvider().get_carbon_intensity(self._geo)
        second = ElectricityMapsProvider().get_carbon_intensity(self._geo)

        assert first == second == 58.7
        assert len(responses.calls) == 1

    @responses.activate
    def test_a_long_run_issues_a_bounded_number_of_requests(self):
        self._add_success_response()

        for _ in range(1000):
            ElectricityMapsProvider().get_carbon_intensity(self._geo)

        assert len(responses.calls) == 1

    @responses.activate
    def test_expired_cache_entry_is_refetched(self):
        self._add_success_response()

        with mock.patch.object(ElectricityMapsProvider, "cache_ttl", 0):
            ElectricityMapsProvider().get_carbon_intensity(self._geo)
            ElectricityMapsProvider().get_carbon_intensity(self._geo)

        assert len(responses.calls) == 2

    @responses.activate
    def test_cache_is_keyed_by_location(self):
        self._add_success_response()

        ElectricityMapsProvider().get_carbon_intensity(self._geo)
        ElectricityMapsProvider().get_carbon_intensity(self._other_geo)

        assert len(responses.calls) == 2

    @responses.activate
    def test_failure_puts_the_api_in_cooldown(self):
        responses.add(
            responses.GET,
            electricitymaps.URL,
            json={"error": "invalid token"},
            status=401,
        )

        with self.assertRaises(electricitymaps.ElectricityMapsAPIError):
            ElectricityMapsProvider().get_carbon_intensity(self._geo)
        for _ in range(100):
            with self.assertRaises(electricitymaps.ElectricityMapsAPIError):
                ElectricityMapsProvider().get_carbon_intensity(self._geo)

        assert len(responses.calls) == 1

    @responses.activate
    def test_cooldown_doubles_on_consecutive_failures_up_to_the_cap(self):
        responses.add(
            responses.GET,
            electricitymaps.URL,
            json={"error": "invalid token"},
            status=401,
        )
        delays = []
        for _ in range(9):
            state = self._only_state()
            if state is not None:
                # Let the previous cooldown expire so the next call hits the API.
                state.cooldown_until = 0.0
            with self.assertRaises(electricitymaps.ElectricityMapsAPIError):
                ElectricityMapsProvider().get_carbon_intensity(self._geo)
            delays.append(self._only_state().cooldown_length)

        assert delays == [30, 60, 120, 240, 480, 960, 1920, 3600, 3600]
        assert len(responses.calls) == 9

    @responses.activate
    def test_cooldown_is_reset_after_a_successful_call(self):
        responses.add(
            responses.GET,
            electricitymaps.URL,
            json={"error": "invalid token"},
            status=401,
        )
        with self.assertRaises(electricitymaps.ElectricityMapsAPIError):
            ElectricityMapsProvider().get_carbon_intensity(self._geo)

        responses.reset()
        self._add_success_response()
        state = self._only_state()
        state.cooldown_until = 0.0
        ElectricityMapsProvider().get_carbon_intensity(self._geo)

        assert state.cooldown_until == state.cooldown_length == 0.0

    @responses.activate
    def test_cooldown_is_not_shared_between_tokens(self):
        responses.add(
            responses.GET,
            electricitymaps.URL,
            json={"error": "invalid token"},
            status=401,
        )
        with self.assertRaises(electricitymaps.ElectricityMapsAPIError):
            ElectricityMapsProvider("bad-token").get_carbon_intensity(self._geo)

        responses.reset()
        self._add_success_response()
        # THEN a tracker with a working token is not blocked by the other's
        # failure cooldown.
        assert ElectricityMapsProvider("good").get_carbon_intensity(self._geo) == 58.7

    @responses.activate
    def test_cache_is_not_shared_between_tokens(self):
        self._add_success_response(carbon_intensity=58.7)
        assert (
            ElectricityMapsProvider("token-a").get_carbon_intensity(self._geo) == 58.7
        )

        responses.reset()
        self._add_success_response(carbon_intensity=412.0)
        # WHEN another tracker in the same process uses a different token, it
        # must not be served the value cached for the first one.
        assert (
            ElectricityMapsProvider("token-b").get_carbon_intensity(self._geo) == 412.0
        )

    @responses.activate
    def test_cooldown_does_not_log_one_error_per_call(self):
        responses.add(
            responses.GET,
            electricitymaps.URL,
            json={"error": "invalid token"},
            status=401,
        )
        emissions = Emissions(
            DataSource(), providers=[ElectricityMapsProvider("bad-token")]
        )
        energy = Energy.from_energy(kWh=1.0)

        with mock.patch("codecarbon.core.emissions.logger") as mock_logger:
            for _ in range(3):
                emissions.get_private_infra_emissions(energy, self._geo)

        # THEN only the first, real failure is an error; the calls skipped
        # during the cooldown stay at debug level.
        assert mock_logger.error.call_count == 1
