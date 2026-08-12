import unittest
from unittest import mock

import responses

from codecarbon.core import electricitymaps_api
from codecarbon.external.geography import GeoMetadata


class TestElectricityMapsCache(unittest.TestCase):
    def setUp(self) -> None:
        # GIVEN
        electricitymaps_api.reset_cache()
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
        electricitymaps_api.reset_cache()

    def _add_success_response(self, carbon_intensity: float = 58.7) -> None:
        responses.add(
            responses.GET,
            electricitymaps_api.URL,
            json={"zone": "FR", "carbonIntensity": carbon_intensity},
            status=200,
        )

    @responses.activate
    def test_second_call_within_ttl_does_not_hit_the_api(self):
        self._add_success_response()

        first = electricitymaps_api.get_carbon_intensity(self._geo)
        second = electricitymaps_api.get_carbon_intensity(self._geo)

        assert first == second == 58.7
        assert len(responses.calls) == 1

    @responses.activate
    def test_a_long_run_issues_a_bounded_number_of_requests(self):
        self._add_success_response()

        for _ in range(1000):
            electricitymaps_api.get_carbon_intensity(self._geo)

        assert len(responses.calls) == 1

    @responses.activate
    def test_expired_cache_entry_is_refetched(self):
        self._add_success_response()

        with mock.patch.object(electricitymaps_api, "ELECTRICITYMAPS_CACHE_TTL", 0):
            electricitymaps_api.get_carbon_intensity(self._geo)
            electricitymaps_api.get_carbon_intensity(self._geo)

        assert len(responses.calls) == 2

    @responses.activate
    def test_cache_is_keyed_by_location(self):
        self._add_success_response()

        electricitymaps_api.get_carbon_intensity(self._geo)
        electricitymaps_api.get_carbon_intensity(self._other_geo)

        assert len(responses.calls) == 2

    @responses.activate
    def test_failure_puts_the_api_in_cooldown(self):
        responses.add(
            responses.GET,
            electricitymaps_api.URL,
            json={"error": "invalid token"},
            status=401,
        )

        with self.assertRaises(electricitymaps_api.ElectricityMapsAPIError):
            electricitymaps_api.get_carbon_intensity(self._geo)
        for _ in range(100):
            with self.assertRaises(electricitymaps_api.ElectricityMapsAPIError):
                electricitymaps_api.get_carbon_intensity(self._geo)

        assert len(responses.calls) == 1

    @responses.activate
    def test_cooldown_doubles_up_to_the_ceiling(self):
        responses.add(
            responses.GET,
            electricitymaps_api.URL,
            json={"error": "invalid token"},
            status=401,
        )

        durations = []
        for _ in range(10):
            with self.assertRaises(electricitymaps_api.ElectricityMapsAPIError):
                electricitymaps_api.get_carbon_intensity(self._geo)
            durations.append(electricitymaps_api._cooldown_duration)
            # Let the cooldown expire so the next call reaches the API again.
            electricitymaps_api._cooldown_until = 0.0

        assert durations[0] == electricitymaps_api.ELECTRICITYMAPS_COOLDOWN_MIN
        assert durations[1] == electricitymaps_api.ELECTRICITYMAPS_COOLDOWN_MIN * 2
        assert durations[-1] == electricitymaps_api.ELECTRICITYMAPS_COOLDOWN_MAX

    @responses.activate
    def test_cooldown_is_reset_after_a_successful_call(self):
        responses.add(
            responses.GET,
            electricitymaps_api.URL,
            json={"error": "invalid token"},
            status=401,
        )
        with self.assertRaises(electricitymaps_api.ElectricityMapsAPIError):
            electricitymaps_api.get_carbon_intensity(self._geo)

        responses.reset()
        self._add_success_response()
        electricitymaps_api._cooldown_until = 0.0
        electricitymaps_api.get_carbon_intensity(self._geo)

        assert electricitymaps_api._cooldown_duration == 0.0
