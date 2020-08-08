import unittest
from unittest import mock

import responses

from co2_tracker.external import CloudMetadata, GeoMetadata, GPUMetadata
from tests.testdata import (
    CLOUD_METADATA_AWS,
    CLOUD_METADATA_AZURE,
    CLOUD_METADATA_GCP,
    GEO_METADATA_USA,
    GEO_METADATA_CANADA,
    TWO_GPU_DETAILS_RESPONSE,
)


class TestCloudMetadata(unittest.TestCase):
    @mock.patch(
        "co2_tracker.external.get_env_cloud_details", return_value=CLOUD_METADATA_AWS
    )
    def test_cloud_metadata_AWS(self, mock_get_env_cloud_details):
        # WHEN
        cloud = CloudMetadata.from_co2_tracker_utils()

        # THEN
        self.assertEqual("aws", cloud.provider)
        self.assertEqual("us-east-1", cloud.region)

    @mock.patch(
        "co2_tracker.external.get_env_cloud_details", return_value=CLOUD_METADATA_AZURE
    )
    def test_cloud_metadata_AZURE(self, mock_get_env_cloud_details):
        # WHEN
        cloud = CloudMetadata.from_co2_tracker_utils()

        # THEN
        self.assertEqual("azure", cloud.provider)
        self.assertEqual("eastus", cloud.region)

    @mock.patch(
        "co2_tracker.external.get_env_cloud_details", return_value=CLOUD_METADATA_GCP
    )
    def test_cloud_metadata_GCP(self, mock_get_env_cloud_details):
        # WHEN
        cloud = CloudMetadata.from_co2_tracker_utils()

        # THEN
        self.assertEqual("gcp", cloud.provider)
        self.assertEqual("us-central1", cloud.region)


class TestGeoMetadata(unittest.TestCase):
    def setUp(self) -> None:
        self.geo_js_url = "https://get.geojs.io/v1/ip/geo.json"

    @responses.activate
    def test_geo_metadata_USA(self):
        responses.add(responses.GET, self.geo_js_url, json=GEO_METADATA_USA, status=200)
        geo = GeoMetadata.from_geo_js(self.geo_js_url)
        self.assertEqual("United States", geo.country)
        self.assertEqual("Illinois", geo.region)

    @responses.activate
    def test_geo_metadata_CANADA(self):
        responses.add(
            responses.GET, self.geo_js_url, json=GEO_METADATA_CANADA, status=200
        )
        geo = GeoMetadata.from_geo_js(self.geo_js_url)
        self.assertEqual("Canada", geo.country)


@mock.patch("co2_tracker.external.is_gpu_details_available", return_value=True)
@mock.patch(
    "co2_tracker.external.get_gpu_details", return_value=TWO_GPU_DETAILS_RESPONSE
)
class TestGPUMetadata(unittest.TestCase):
    def test_gpu_metadata_is_gpu_available(
        self, mocked_get_gpu_details, mocked_is_gpu_details_available
    ):
        gpu = GPUMetadata.from_co2_tracker_utils()
        self.assertTrue(gpu.is_gpu_available)

    def test_gpu_metadata_total_power(
        self, mocked_get_gpu_details, mocked_is_gpu_details_available
    ):
        gpu = GPUMetadata.from_co2_tracker_utils()
        self.assertAlmostEqual(0.074318, gpu.total_power.kw, places=2)

    def test_gpu_metadata_one_gpu_power(
        self, mocked_get_gpu_details, mocked_is_gpu_details_available
    ):
        gpu = GPUMetadata.from_co2_tracker_utils()
        self.assertAlmostEqual(
            0.032159, gpu.get_power_for_gpus(gpu_ids=[1]).kw, places=2
        )
