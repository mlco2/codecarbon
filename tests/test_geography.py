import unittest
from unittest import mock

import requests
import responses

from codecarbon.external.geography import (
    GEO_API_TIMEOUT,
    CloudMetadata,
    GeoMetadata,
)
from tests.testdata import (
    CLOUD_METADATA_AWS,
    CLOUD_METADATA_AZURE,
    CLOUD_METADATA_GCP,
    CLOUD_METADATA_GCP_EMPTY,
    GEO_METADATA_CANADA,
    GEO_METADATA_USA,
    GEO_METADATA_USA_BACKUP,
)


class TestCloudMetadata(unittest.TestCase):
    @mock.patch(
        "codecarbon.external.geography.get_env_cloud_details",
        return_value=CLOUD_METADATA_AWS,
    )
    def test_cloud_metadata_AWS(self, mock_get_env_cloud_details):
        # WHEN
        cloud = CloudMetadata.from_utils()

        # THEN
        # AWS in not considered a cloud provider for CodeCarbon as it does not provide carbon intensity
        # self.assertEqual("aws", cloud.provider)
        # self.assertEqual("us-east-1", cloud.region)
        self.assertEqual(None, cloud.provider)
        self.assertEqual(None, cloud.region)

    @mock.patch(
        "codecarbon.external.geography.get_env_cloud_details",
        return_value=CLOUD_METADATA_AZURE,
    )
    def test_cloud_metadata_AZURE(self, mock_get_env_cloud_details):
        # WHEN
        cloud = CloudMetadata.from_utils()

        # THEN
        # Azure in not considered a cloud provider for CodeCarbon as it does not provide carbon intensity
        # self.assertEqual("azure", cloud.provider)
        # self.assertEqual("eastus", cloud.region)
        self.assertEqual(None, cloud.provider)
        self.assertEqual(None, cloud.region)

    @mock.patch(
        "codecarbon.external.geography.get_env_cloud_details",
        return_value=CLOUD_METADATA_GCP,
    )
    def test_cloud_metadata_GCP(self, mock_get_env_cloud_details):
        # WHEN
        cloud = CloudMetadata.from_utils()

        # THEN
        self.assertEqual("gcp", cloud.provider)
        self.assertEqual("us-central1", cloud.region)

    @mock.patch(
        "codecarbon.external.geography.get_env_cloud_details",
        return_value=CLOUD_METADATA_GCP_EMPTY,
    )
    def test_cloud_metadata_GCP_empty(self, mock_get_env_cloud_details):
        # WHEN
        cloud = CloudMetadata.from_utils()

        # THEN
        self.assertIsNone(cloud.provider)
        self.assertIsNone(cloud.region)


class TestGeoMetadata(unittest.TestCase):
    def setUp(self) -> None:
        self.geo_js_url = "https://get.geojs.io/v1/ip/geo.json"

    @responses.activate
    def test_geo_metadata_USA(self):
        responses.add(responses.GET, self.geo_js_url, json=GEO_METADATA_USA, status=200)
        geo = GeoMetadata.from_geo_js(self.geo_js_url)
        self.assertEqual("USA", geo.country_iso_code)
        self.assertEqual("United States", geo.country_name)
        self.assertEqual("illinois", geo.region)

    @responses.activate
    def test_geo_metadata_USA_backup(self):
        responses.add(
            responses.GET, self.geo_js_url, json={"error": "not found"}, status=404
        )
        responses.add(
            responses.GET,
            "https://ipinfo.io/json",
            json=GEO_METADATA_USA_BACKUP,
            status=200,
        )
        geo = GeoMetadata.from_geo_js(self.geo_js_url)
        self.assertEqual("USA", geo.country_iso_code)
        self.assertEqual("United States", geo.country_name)
        self.assertEqual("illinois", geo.region)

    @responses.activate
    def test_geo_metadata_empty_region_fallback(self):
        empty_region_response = GEO_METADATA_USA.copy()
        empty_region_response["region"] = ""

        responses.add(
            responses.GET, self.geo_js_url, json=empty_region_response, status=200
        )
        responses.add(
            responses.GET,
            "https://ipinfo.io/json",
            json=GEO_METADATA_USA_BACKUP,
            status=200,
        )
        geo = GeoMetadata.from_geo_js(self.geo_js_url)
        self.assertEqual("USA", geo.country_iso_code)
        self.assertEqual("United States", geo.country_name)
        self.assertEqual("illinois", geo.region)

    @responses.activate
    def test_geo_metadata_retries_primary_api_on_timeout(self):
        responses.add(
            responses.GET,
            self.geo_js_url,
            body=requests.exceptions.Timeout("Read timed out"),
        )
        responses.add(responses.GET, self.geo_js_url, json=GEO_METADATA_USA, status=200)
        responses.add(
            responses.GET,
            "https://ipinfo.io/json",
            json=GEO_METADATA_USA_BACKUP,
            status=200,
        )

        geo = GeoMetadata.from_geo_js(self.geo_js_url)

        self.assertEqual("USA", geo.country_iso_code)
        self.assertEqual("illinois", geo.region)
        # The primary API answered on the second try, so the backup is never called.
        self.assertEqual(
            [self.geo_js_url, self.geo_js_url],
            [call.request.url for call in responses.calls],
        )

    def test_geo_metadata_uses_configured_timeout(self):
        mocked_response = mock.Mock()
        mocked_response.json.return_value = GEO_METADATA_USA

        with mock.patch(
            "codecarbon.external.geography.requests.get", return_value=mocked_response
        ) as mocked_get:
            geo = GeoMetadata.from_geo_js(self.geo_js_url)

        self.assertEqual("USA", geo.country_iso_code)
        self.assertGreater(GEO_API_TIMEOUT, 0.5)
        mocked_get.assert_called_once_with(self.geo_js_url, timeout=GEO_API_TIMEOUT)

    @responses.activate
    def test_geo_metadata_CANADA(self):
        responses.add(
            responses.GET, self.geo_js_url, json=GEO_METADATA_CANADA, status=200
        )
        geo = GeoMetadata.from_geo_js(self.geo_js_url)
        self.assertEqual("CAN", geo.country_iso_code)
        self.assertEqual("Canada", geo.country_name)
        self.assertEqual("ontario", geo.region)
