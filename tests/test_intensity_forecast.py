import unittest
from datetime import datetime, timedelta, timezone

import responses

from codecarbon.core import electricitymaps_api
from codecarbon.core.intensity_forecast import (
    Forecast,
    IntensityPoint,
    best_window,
    get_forecast,
)
from codecarbon.external.geography import GeoMetadata

BASE = datetime(2026, 8, 13, 0, 0, tzinfo=timezone.utc)


def _forecast(values):
    return Forecast(
        zone="FR",
        points=[
            IntensityPoint(at=BASE + timedelta(hours=i), g_co2e_per_kwh=v)
            for i, v in enumerate(values)
        ],
    )


def _payload(values, start=None):
    start = start or datetime.now(timezone.utc)
    return {
        "zone": "FR",
        "forecast": [
            {
                "datetime": (start + timedelta(hours=i))
                .isoformat()
                .replace("+00:00", "Z"),
                "carbonIntensity": v,
            }
            for i, v in enumerate(values)
        ],
    }


class TestGetForecast(unittest.TestCase):
    def setUp(self) -> None:
        # The forecast shares the Electricity Maps failure cooldown with the
        # current-intensity path, so a failing test must not starve the next.
        electricitymaps_api.reset_cache()
        self.addCleanup(electricitymaps_api.reset_cache)
        self._geo = GeoMetadata(
            country_iso_code="FRA",
            country_name="France",
            region=None,
            country_2letter_iso_code="FR",
        )
        self._geo_latlon = GeoMetadata(
            country_iso_code="FRA",
            country_name="France",
            region=None,
            country_2letter_iso_code="FR",
            latitude=48.85,
            longitude=2.35,
        )

    def test_no_token_returns_none_without_calling_api(self):
        assert get_forecast(self._geo, token=None) is None

    @responses.activate
    def test_shared_cooldown_skips_the_request(self):
        # A failure on the current-intensity path must back the forecast off
        # too: no HTTP request, and still a None instead of a raise.
        electricitymaps_api._start_cooldown(
            electricitymaps_api._cache_key(
                electricitymaps_api.location_params(self._geo), "tok"
            )
        )
        responses.add(
            responses.GET,
            electricitymaps_api.FORECAST_URL,
            json=_payload([100]),
            status=200,
        )
        assert get_forecast(self._geo, token="tok") is None
        assert len(responses.calls) == 0

    @responses.activate
    def test_parses_forecast(self):
        responses.add(
            responses.GET,
            electricitymaps_api.FORECAST_URL,
            json=_payload([100, 200, 50]),
            status=200,
        )
        forecast = get_forecast(self._geo, token="tok")
        assert forecast is not None
        assert forecast.zone == "FR"
        assert [p.g_co2e_per_kwh for p in forecast.points] == [100, 200, 50]
        assert all(p.at.tzinfo is not None for p in forecast.points)
        assert responses.calls[0].request.headers["auth-token"] == "tok"
        assert "countryCode=FR" in responses.calls[0].request.url

    @responses.activate
    def test_uses_lat_lon_when_available(self):
        responses.add(
            responses.GET,
            electricitymaps_api.FORECAST_URL,
            json=_payload([100]),
            status=200,
        )
        get_forecast(self._geo_latlon, token="tok")
        url = responses.calls[0].request.url
        assert "lat=48.85" in url and "lon=2.35" in url

    @responses.activate
    def test_naive_timestamps_are_treated_as_utc(self):
        payload = _payload([100])
        payload["forecast"][0]["datetime"] = "2999-01-01T03:00:00"
        responses.add(
            responses.GET,
            electricitymaps_api.FORECAST_URL,
            json=payload,
            status=200,
        )
        forecast = get_forecast(self._geo, token="tok", horizon_hours=24 * 365 * 1000)
        assert forecast.points[0].at.tzinfo == timezone.utc

    @responses.activate
    def test_horizon_truncates_points(self):
        responses.add(
            responses.GET,
            electricitymaps_api.FORECAST_URL,
            json=_payload([100, 200, 300, 400]),
            status=200,
        )
        forecast = get_forecast(self._geo, token="tok", horizon_hours=2)
        assert len(forecast.points) <= 3

    @responses.activate
    def test_error_status_returns_none(self):
        responses.add(
            responses.GET,
            electricitymaps_api.FORECAST_URL,
            json={"error": "no access"},
            status=403,
        )
        assert get_forecast(self._geo, token="tok") is None

    @responses.activate
    def test_malformed_payload_returns_none(self):
        responses.add(
            responses.GET,
            electricitymaps_api.FORECAST_URL,
            json={"unexpected": True},
            status=200,
        )
        assert get_forecast(self._geo, token="tok") is None

    @responses.activate
    def test_empty_forecast_returns_none(self):
        responses.add(
            responses.GET,
            electricitymaps_api.FORECAST_URL,
            json={"zone": "FR", "forecast": []},
            status=200,
        )
        assert get_forecast(self._geo, token="tok") is None


class TestBestWindow(unittest.TestCase):
    def test_picks_the_trough(self):
        forecast = _forecast([300, 250, 100, 90, 280, 300])
        start, mean = best_window(forecast, timedelta(hours=2))
        assert start == BASE + timedelta(hours=2)
        assert mean == 95

    def test_flat_series_picks_now(self):
        forecast = _forecast([200] * 5)
        start, mean = best_window(forecast, timedelta(hours=2))
        assert start == BASE
        assert mean == 200

    def test_decreasing_series_picks_last_complete_window(self):
        forecast = _forecast([500, 400, 300, 200, 100])
        start, _ = best_window(forecast, timedelta(hours=2))
        assert start == BASE + timedelta(hours=3)

    def test_deadline_before_the_next_point_leaves_only_now(self):
        forecast = _forecast([300, 100, 100])
        start, mean = best_window(
            forecast, timedelta(hours=2), deadline=BASE + timedelta(minutes=30)
        )
        assert start == BASE
        assert mean == 200

    def test_deadline_caps_the_start_time_not_the_end(self):
        # The deadline is the latest acceptable start: a window starting at it
        # is allowed even though it finishes afterwards.
        forecast = _forecast([300, 200, 50, 50])
        start, mean = best_window(
            forecast, timedelta(hours=2), deadline=BASE + timedelta(hours=2)
        )
        assert start == BASE + timedelta(hours=2)
        assert mean == 50

    def test_deadline_restricts_the_search(self):
        forecast = _forecast([300, 200, 50, 50])
        start, _ = best_window(
            forecast, timedelta(hours=1), deadline=BASE + timedelta(hours=1)
        )
        assert start == BASE + timedelta(hours=1)

    def test_duration_longer_than_horizon_falls_back_to_now(self):
        forecast = _forecast([300, 100])
        start, mean = best_window(forecast, timedelta(hours=10))
        assert start == BASE
        assert mean == 300

    def test_partial_last_hour_is_weighted_by_overlap(self):
        # 90 minutes over hourly points: the second hour only counts for half.
        forecast = _forecast([100, 300, 300])
        start, mean = best_window(forecast, timedelta(minutes=90))
        assert start == BASE
        assert mean == (100 * 60 + 300 * 30) / 90

    def test_irregular_gaps_do_not_stretch_the_coverage(self):
        points = [
            IntensityPoint(at=BASE, g_co2e_per_kwh=300),
            IntensityPoint(at=BASE + timedelta(hours=3), g_co2e_per_kwh=100),
            IntensityPoint(at=BASE + timedelta(hours=4), g_co2e_per_kwh=50),
        ]
        forecast = Forecast(zone="FR", points=points)
        # The forecast covers one hour, not three, past its last point, so the
        # cheapest-looking window (starting at the last point) is not complete.
        start, _ = best_window(forecast, timedelta(hours=2))
        assert start == BASE + timedelta(hours=3)
