import unittest
from unittest import mock

from codecarbon.external.hardware import GPU
from tests.testdata import TWO_GPU_DETAILS_RESPONSE


@mock.patch("codecarbon.core.gpu.is_gpu_details_available", return_value=True)
@mock.patch(
    "codecarbon.external.hardware.get_gpu_details",
    return_value=TWO_GPU_DETAILS_RESPONSE,
)
class TestGPUMetadata(unittest.TestCase):
    def test_gpu_metadata_total_power(
        self,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
    ):
        gpu = GPU.from_utils()
        self.assertAlmostEqual(0.074318, gpu.total_power().kW, places=2)

    def test_gpu_metadata_one_gpu_power(
        self,
        mocked_get_gpu_details,
        mocked_is_gpu_details_available,
    ):
        gpu = GPU.from_utils()
        self.assertAlmostEqual(
            0.032159,
            gpu._get_power_for_gpus(gpu_ids=[1]).kW,
            places=2,
        )
