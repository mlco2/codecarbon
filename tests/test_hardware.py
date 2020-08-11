import unittest
from unittest import mock

from co2_tracker.external.hardware import GPU

from tests.testdata import TWO_GPU_DETAILS_RESPONSE


@mock.patch("co2_tracker.co2_tracker.is_gpu_details_available", return_value=True)
@mock.patch(
    "co2_tracker.external.hardware.get_gpu_details",
    return_value=TWO_GPU_DETAILS_RESPONSE,
)
class TestGPUMetadata(unittest.TestCase):
    def test_gpu_metadata_total_power(
        self, mocked_get_gpu_details, mocked_is_gpu_details_available
    ):
        gpu = GPU.from_co2_tracker_utils()
        self.assertAlmostEqual(0.074318, gpu.total_power.kw, places=2)

    def test_gpu_metadata_one_gpu_power(
        self, mocked_get_gpu_details, mocked_is_gpu_details_available
    ):
        gpu = GPU.from_co2_tracker_utils()
        self.assertAlmostEqual(
            0.032159, gpu.get_power_for_gpus(gpu_ids=[1]).kw, places=2
        )
