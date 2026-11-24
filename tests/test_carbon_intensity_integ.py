"""
Integration tests for the live carbon intensity providers, against the real APIs.

Excluded from ``uv run task test-package``. Run them with:

    uv run task test-carbon-intensity-integ

National Grid ESO needs no key. The Electricity Maps tests that need a valid
token are skipped unless ``CODECARBON_ELECTRICITYMAPS_API_TOKEN`` is set, the
same variable CodeCarbon reads (a free personal token is enough).

Grid intensity changes all the time, so values are only checked to be
plausible; the tests check which source answered and how many requests it took.
"""

import os
import time
from collections import Counter
from unittest import mock

import pytest
import requests

from codecarbon import OfflineEmissionsTracker
from codecarbon.core.carbon_intensity import (
    ElectricityMapsProvider,
    NationalGridESOProvider,
    build_providers,
)
from codecarbon.core.carbon_intensity.electricitymaps import ElectricityMapsAPIError
from codecarbon.core.emissions import Emissions
from codecarbon.core.units import Energy
from codecarbon.external.geography import GeoMetadata
from codecarbon.input import DataSource

pytestmark = pytest.mark.integ_test

EM_TOKEN = os.environ.get("CODECARBON_ELECTRICITYMAPS_API_TOKEN", "")
needs_em_token = pytest.mark.skipif(
    not EM_TOKEN,
    reason="set CODECARBON_ELECTRICITYMAPS_API_TOKEN to run Electricity Maps tests",
)

EM_HOST = "api.electricitymaps.com"
ESO_HOST = "api.carbonintensity.org.uk"

GBR = GeoMetadata(
    country_iso_code="GBR", country_name="United Kingdom", country_2letter_iso_code="GB"
)
FRA = GeoMetadata(
    country_iso_code="FRA", country_name="France", country_2letter_iso_code="FR"
)
PARIS = GeoMetadata(
    country_iso_code="FRA",
    country_name="France",
    country_2letter_iso_code="FR",
    latitude=48.8566,
    longitude=2.3522,
)
ONE_KWH = Energy.from_energy(kWh=1)


def assert_plausible(g_per_kwh):
    # Real grids range from ~0 (hydro, nuclear) to ~1000 (coal) gCO2e/kWh.
    assert 0 <= g_per_kwh < 1500, g_per_kwh


@pytest.fixture(autouse=True)
def fresh_caches():
    ElectricityMapsProvider.reset_cache()
    NationalGridESOProvider.reset_cache()
    yield
    ElectricityMapsProvider.reset_cache()
    NationalGridESOProvider.reset_cache()


@pytest.fixture
def http_calls():
    """Count the real requests made, per host, without mocking them."""
    calls = Counter()
    real_get = requests.get

    def counting_get(url, *args, **kwargs):
        calls[url.split("/")[2]] += 1
        return real_get(url, *args, **kwargs)

    with mock.patch.object(requests, "get", counting_get):
        yield calls


def private_infra_g_per_kwh(conf, geo):
    emissions = Emissions(DataSource(), providers=build_providers(conf))
    return emissions.get_private_infra_emissions(ONE_KWH, geo) * 1000


def run_tracker(**kwargs):
    """Run a short offline tracker and return its implied gCO2e/kWh."""
    tracker = OfflineEmissionsTracker(
        measure_power_secs=1,
        save_to_file=False,
        allow_multiple_runs=True,
        log_level="error",
        **kwargs,
    )
    tracker.start()
    time.sleep(2)
    kg = tracker.stop()
    energy = tracker.final_emissions_data.energy_consumed
    assert energy > 0
    return kg / energy * 1000


# ----------------------------------------------------------------------
# National Grid ESO (no key needed)
# ----------------------------------------------------------------------


def test_national_grid_eso_returns_live_intensity(http_calls):
    provider = NationalGridESOProvider()

    first = provider.get_carbon_intensity(GBR)
    second = provider.get_carbon_intensity(GBR)

    assert_plausible(first)
    assert second == first
    assert http_calls == {ESO_HOST: 1}  # the second call is cached


def test_national_grid_eso_is_not_queried_outside_great_britain(http_calls):
    static = private_infra_g_per_kwh({}, FRA)

    result = private_infra_g_per_kwh({"use_national_grid_eso_api": True}, FRA)

    assert result == pytest.approx(static)
    assert http_calls == {}


def test_tracker_uses_national_grid_eso_in_great_britain(http_calls, monkeypatch):
    # Trackers read the token from the environment, and Electricity Maps would
    # then answer before ESO.
    monkeypatch.delenv("CODECARBON_ELECTRICITYMAPS_API_TOKEN", raising=False)
    live = NationalGridESOProvider().get_carbon_intensity(GBR)

    implied = run_tracker(country_iso_code="GBR", use_national_grid_eso_api=True)

    assert implied == pytest.approx(live)
    assert http_calls == {ESO_HOST: 1}


# ----------------------------------------------------------------------
# Electricity Maps
# ----------------------------------------------------------------------


def test_electricitymaps_rejects_an_invalid_token(http_calls):
    # Needs no real token: checks the live API's error is surfaced and the
    # cooldown stops the retries.
    provider = ElectricityMapsProvider("invalid-token-for-integration-test")

    with pytest.raises(ElectricityMapsAPIError):
        provider.get_carbon_intensity(FRA)
    with pytest.raises(ElectricityMapsAPIError):
        provider.get_carbon_intensity(FRA)

    assert http_calls == {EM_HOST: 1}


def test_invalid_electricitymaps_token_falls_back_to_national_grid_eso(http_calls):
    live_eso = NationalGridESOProvider().get_carbon_intensity(GBR)

    result = private_infra_g_per_kwh(
        {
            "electricitymaps_api_token": "invalid-token-for-integration-test",
            "use_national_grid_eso_api": True,
        },
        GBR,
    )

    assert result == pytest.approx(live_eso)
    assert http_calls == {EM_HOST: 1, ESO_HOST: 1}


@needs_em_token
@pytest.mark.parametrize("geo", [FRA, GBR, PARIS], ids=["FR", "GB", "lat-lon"])
def test_electricitymaps_returns_live_intensity(geo, http_calls):
    provider = ElectricityMapsProvider(EM_TOKEN)

    first = provider.get_carbon_intensity(geo)
    second = provider.get_carbon_intensity(geo)

    assert_plausible(first)
    assert second == first
    assert http_calls == {EM_HOST: 1}


@needs_em_token
def test_electricitymaps_takes_priority_over_national_grid_eso(http_calls):
    live_em = ElectricityMapsProvider(EM_TOKEN).get_carbon_intensity(GBR)

    result = private_infra_g_per_kwh(
        {"electricitymaps_api_token": EM_TOKEN, "use_national_grid_eso_api": True},
        GBR,
    )

    assert result == pytest.approx(live_em)
    assert http_calls == {EM_HOST: 1}  # ESO is never called


@needs_em_token
def test_tracker_reads_electricitymaps_token_from_env_config(http_calls):
    live_em = ElectricityMapsProvider(EM_TOKEN).get_carbon_intensity(FRA)

    # No token argument: the tracker gets it from CodeCarbon's env config.
    # Both country codes are passed: the offline tracker does not derive the
    # 2-letter code that Electricity Maps is queried with.
    implied = run_tracker(country_iso_code="FRA", country_2letter_iso_code="FR")

    assert implied == pytest.approx(live_em)
    assert http_calls == {EM_HOST: 1}
