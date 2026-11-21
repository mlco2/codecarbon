from typing import Any, Hashable, Mapping, Optional

import requests

from codecarbon.core.carbon_intensity.base import (
    CarbonIntensityCooldownError,
    CarbonIntensityError,
    CarbonIntensityProvider,
)
from codecarbon.external.geography import GeoMetadata

# National Grid ESO Carbon Intensity API for Great Britain.
# Data source: https://carbonintensity.org.uk/ — published by National Grid ESO
# under the Open Government Licence v3.0. The API reports a single,
# national-level (Great-Britain-wide) carbon intensity figure; it does not
# provide regional or sub-national granularity.
URL: str = "https://api.carbonintensity.org.uk/intensity"

# Kept short deliberately: this call sits in the emissions fallback chain and
# must not stall a measurement if the API is slow or unreachable.
NATIONAL_GRID_ESO_API_TIMEOUT: int = 4

NATIONAL_GRID_ESO_CACHE_TTL: int = 300
NATIONAL_GRID_ESO_COOLDOWN: int = 30
NATIONAL_GRID_ESO_MAX_COOLDOWN: int = 3600


class NationalGridESOAPIError(CarbonIntensityError):
    pass


class NationalGridESOAPICooldownError(
    NationalGridESOAPIError, CarbonIntensityCooldownError
):
    """The request was skipped because a recent one failed."""


class NationalGridESOProvider(CarbonIntensityProvider):
    """
    Live, Great-Britain-wide carbon intensity from the National Grid ESO
    Carbon Intensity API. Opt-in with ``use_national_grid_eso_api``.
    """

    name = "National Grid ESO"
    cache_ttl = NATIONAL_GRID_ESO_CACHE_TTL
    cooldown = NATIONAL_GRID_ESO_COOLDOWN
    max_cooldown = NATIONAL_GRID_ESO_MAX_COOLDOWN
    error_class = NationalGridESOAPIError
    cooldown_error_class = NationalGridESOAPICooldownError

    @classmethod
    def from_config(
        cls, conf: Mapping[str, Any]
    ) -> Optional["NationalGridESOProvider"]:
        # Opt-in only: it makes a live network call on every GB run.
        return cls() if conf.get("use_national_grid_eso_api") else None

    def is_supported(self, geo: GeoMetadata) -> bool:
        """
        Return True when the location is in Great Britain.

        The API covers the GB grid (England, Scotland, Wales) only. Northern
        Ireland shares the ISO code GBR but is on the all-island Irish grid, so
        it keeps CodeCarbon's static data.
        """
        if geo.country_iso_code != "GBR":
            return False
        return (geo.region or "").strip() != "northern ireland"

    def _cache_key(self, geo: GeoMetadata) -> Hashable:
        # The API only ever describes Great Britain as a whole.
        return None

    def _fetch(self, geo: GeoMetadata) -> float:
        resp = requests.get(URL, timeout=NATIONAL_GRID_ESO_API_TIMEOUT)
        if resp.status_code != 200:
            raise NationalGridESOAPIError(
                f"National Grid ESO API returned status {resp.status_code}"
            )

        try:
            intensity = resp.json()["data"][0]["intensity"]
            # Prefer actual; fall back to forecast when actual is not published yet.
            actual = intensity.get("actual")
            carbon_intensity_g_per_kWh = (
                actual if actual is not None else intensity.get("forecast")
            )
        except (ValueError, KeyError, IndexError, TypeError, AttributeError) as e:
            # ValueError: body is not JSON (e.g. a captive portal's HTML page).
            # AttributeError: "intensity" is null or not an object.
            raise NationalGridESOAPIError(f"Unexpected response structure: {e}") from e

        if carbon_intensity_g_per_kWh is None:
            raise NationalGridESOAPIError(
                "No actual or forecast carbon intensity in response"
            )

        return carbon_intensity_g_per_kWh
