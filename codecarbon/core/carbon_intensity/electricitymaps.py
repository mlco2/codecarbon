from typing import Any, Dict, Hashable, Mapping, Optional

import requests

from codecarbon.core.carbon_intensity.base import (
    CarbonIntensityCooldownError,
    CarbonIntensityError,
    CarbonIntensityProvider,
)
from codecarbon.external.geography import GeoMetadata

URL: str = "https://api.electricitymaps.com/v3/carbon-intensity/latest"
# Kept short: the lookup runs on the measurement thread, which stop() joins.
ELECTRICITYMAPS_API_TIMEOUT: int = 10

ELECTRICITYMAPS_CACHE_TTL: int = 60
ELECTRICITYMAPS_COOLDOWN: int = 30
ELECTRICITYMAPS_MAX_COOLDOWN: int = 3600


class ElectricityMapsAPIError(CarbonIntensityError):
    pass


class ElectricityMapsAPICooldownError(
    ElectricityMapsAPIError, CarbonIntensityCooldownError
):
    """Raised when a request is skipped because a previous one failed."""


class ElectricityMapsProvider(CarbonIntensityProvider):
    """
    Live carbon intensity from the Electricity Maps API (formerly CO2 Signal),
    by latitude/longitude or country code. Enabled by an API token.
    """

    name = "Electricity Maps"
    cache_ttl = ELECTRICITYMAPS_CACHE_TTL
    cooldown = ELECTRICITYMAPS_COOLDOWN
    max_cooldown = ELECTRICITYMAPS_MAX_COOLDOWN
    error_class = ElectricityMapsAPIError
    cooldown_error_class = ElectricityMapsAPICooldownError

    def __init__(self, api_token: str = ""):
        self.api_token = api_token

    @classmethod
    def from_config(
        cls, conf: Mapping[str, Any]
    ) -> Optional["ElectricityMapsProvider"]:
        token = conf.get("electricitymaps_api_token")
        return cls(token) if token else None

    @staticmethod
    def _params(geo: GeoMetadata) -> Dict[str, Any]:
        if geo.latitude is not None:
            return {"lat": geo.latitude, "lon": geo.longitude}
        return {"countryCode": geo.country_2letter_iso_code}

    def _cache_key(self, geo: GeoMetadata) -> Hashable:
        # Keyed by token too: one tracker's bad token must not put another's
        # good one in cooldown, nor be served the other's cached value.
        return (tuple(sorted(self._params(geo).items())), self.api_token)

    def _fetch(self, geo: GeoMetadata) -> float:
        resp = requests.get(
            URL,
            params=self._params(geo),
            headers={"auth-token": self.api_token},
            timeout=ELECTRICITYMAPS_API_TIMEOUT,
        )
        if resp.status_code != 200:
            try:
                body = resp.json()
            except ValueError:
                body = {}
            raise ElectricityMapsAPIError(
                body.get("error") or body.get("message") or resp.text
            )
        # API v3 response structure: carbonIntensity is at the root level
        carbon_intensity_g_per_kWh = resp.json().get("carbonIntensity")
        if carbon_intensity_g_per_kWh is None:
            raise ElectricityMapsAPIError("No carbonIntensity data in response")
        return carbon_intensity_g_per_kWh
