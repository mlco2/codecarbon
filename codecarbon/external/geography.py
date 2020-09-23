"""
Encapsulates external dependencies to retrieve cloud and geographical metadata
"""

from dataclasses import dataclass
import logging
import re
import requests
from typing import Callable, Dict, Optional

from codecarbon.core.cloud import get_env_cloud_details

logger = logging.getLogger(__name__)


@dataclass
class CloudMetadata:

    provider: Optional[str]
    region: Optional[str]

    @property
    def is_on_private_infra(self) -> bool:
        return self.provider is None and self.region is None

    @classmethod
    def from_utils(cls) -> "CloudMetadata":
        def extract_gcp_region(zone: str) -> str:
            """
            projects/705208488469/zones/us-central1-a -> us-central1
            """
            google_region_regex = r"[a-z]+-[a-z]+[0-9]"
            return re.search(google_region_regex, zone).group(0)

        extract_region_for_provider: Dict[str, Callable] = {
            "aws": lambda x: x["metadata"]["region"],
            "azure": lambda x: x["metadata"]["compute"]["location"],
            "gcp": lambda x: extract_gcp_region(x["metadata"]["zone"]),
        }

        cloud_metadata: Dict = get_env_cloud_details()

        if cloud_metadata is None:
            return cls(provider=None, region=None)

        provider: str = cloud_metadata["provider"].lower()
        region: str = extract_region_for_provider.get(provider)(cloud_metadata)

        return cls(provider=provider, region=region)


class GeoMetadata:
    def __init__(
        self,
        country_iso_code: str,
        country_name: Optional[str] = None,
        region: Optional[str] = None,
    ):
        self.country_iso_code = country_iso_code.upper()
        self.country_name = country_name
        self.region = region if region is None else region.lower()

    def __repr__(self) -> str:
        return "GeoMetadata({}={}, {}={}, {}={})".format(
            "country_iso_code",
            self.country_iso_code,
            "country_name",
            self.country_name,
            "region",
            self.region,
        )

    @classmethod
    def from_geo_js(cls, url: str) -> "GeoMetadata":
        try:
            response: Dict = requests.get(url, timeout=0.5).json()
        except requests.exceptions.Timeout:
            # If there is a timeout, we default to Canada
            logger.info(
                "Unable to access geographical location. Using 'Canada' as the default value"
            )
            return cls(country_iso_code="CAN", country_name="Canada")
        return cls(
            country_iso_code=response["country_code3"].upper(),
            country_name=response["country"],
            region=response.get("region", "").lower(),
        )
