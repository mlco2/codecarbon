"""
Encapsulates external dependencies to retrieve cloud and geographical metadata
"""

import re
import urllib.parse
from dataclasses import dataclass
from typing import Callable, Dict, Optional

import requests

from codecarbon.core.cloud import get_env_cloud_details
from codecarbon.external.logger import logger


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
            "aws": lambda x: x["metadata"].get("region"),
            "azure": lambda x: x["metadata"]["compute"].get("location"),
            "gcp": lambda x: extract_gcp_region(x["metadata"].get("zone")),
        }

        cloud_metadata: Dict = get_env_cloud_details()

        if cloud_metadata is None or cloud_metadata["metadata"] == {}:
            return cls(provider=None, region=None)

        provider: str = cloud_metadata["provider"].lower()
        region: str = extract_region_for_provider.get(provider)(cloud_metadata)
        if region is None:
            logger.warning(
                f"Cloud provider '{provider}' detected, but unable to read region. Using country value instead."
            )
        if provider in ["aws", "azure"]:
            logger.warning(
                f"Cloud provider '{provider}' do not publish electricity carbon intensity. Using country value instead."
            )
            provider = None
            region = None
        return cls(provider=provider, region=region)


class GeoMetadata:
    def __init__(
        self,
        country_iso_code: str,
        country_name: Optional[str] = None,
        region: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        country_2letter_iso_code: Optional[str] = None,
    ):
        self.country_iso_code = (
            None if country_iso_code is None else country_iso_code.upper()
        )
        self.country_name = country_name
        self.region = region if region is None else region.lower()
        self.latitude = latitude
        self.longitude = longitude
        self.country_2letter_iso_code = (
            country_2letter_iso_code.upper() if country_2letter_iso_code else None
        )

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

            return cls(
                country_iso_code=response["country_code3"].upper(),
                country_name=response["country"],
                region=response.get("region", "").lower(),
                latitude=float(response.get("latitude")),
                longitude=float(response.get("longitude")),
                country_2letter_iso_code=response.get("country_code"),
            )
        except Exception as e:
            # If there is a timeout, we will try using a backup API
            logger.warning(
                f"Unable to access geographical location through primary API. Will resort to using the backup API - Exception : {e} - url={url}"
            )

        geo_url_backup = "https://ip-api.com/json/"

        try:
            geo_response: Dict = requests.get(geo_url_backup, timeout=0.5).json()
            country_name = geo_response["country"]

            # The previous request does not return the three-letter country code
            country_code_3_url = f"https://api.first.org/data/v1/countries?q={urllib.parse.quote_plus(country_name)}&scope=iso"
            country_code_response: Dict = requests.get(
                country_code_3_url, timeout=0.5
            ).json()

            return cls(
                country_iso_code=next(
                    iter(country_code_response["data"].keys())
                ).upper(),
                country_name=country_name,
                region=geo_response.get("regionName", "").lower(),
                latitude=float(geo_response.get("lat")),
                longitude=float(geo_response.get("lon")),
                country_2letter_iso_code=geo_response.get("countryCode"),
            )
        except Exception as e:
            # If both API calls fail, default to Canada
            logger.warning(
                f"Unable to access geographical location. Using 'Canada' as the default value - Exception : {e} - url={url}"
            )

            return cls(
                country_iso_code="CAN",
                country_name="Canada",
                region="Quebec",
                latitude=46.8,
                longitude=-71.2,
                country_2letter_iso_code="CA",
            )
