#!/usr/bin/env python3
"""
Tests for OneClickImpact carbon offset integration
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from codecarbon.emissions_tracker import EmissionsTracker, track_emissions
from codecarbon.external.geography import CloudMetadata
from codecarbon.output_methods.emissions_data import EmissionsData
from codecarbon.output_methods.offset import OneClickImpactOutput
from tests.fake_modules import pynvml as fake_pynvml
from tests.testdata import (
    GEO_METADATA_CANADA,
    TWO_GPU_DETAILS_RESPONSE,
    TWO_GPU_DETAILS_RESPONSE_HANDLES,
)

TEST_API_KEY = "test_key"


@patch("codecarbon.core.gpu.pynvml", fake_pynvml)
@patch("codecarbon.core.gpu.is_gpu_details_available", return_value=True)
@patch(
    "codecarbon.external.hardware.AllGPUDevices.get_gpu_details",
    return_value=TWO_GPU_DETAILS_RESPONSE,
)
@patch(
    "codecarbon.emissions_tracker.EmissionsTracker._get_cloud_metadata",
    return_value=CloudMetadata(provider=None, region=None),
)
@patch("codecarbon.core.cpu.IntelPowerGadget._log_values")
@patch("codecarbon.core.cpu.IntelPowerGadget._setup_cli")
class TestOneClickImpactIntegration(unittest.TestCase):

    def setUp(self):
        fake_pynvml.DETAILS = TWO_GPU_DETAILS_RESPONSE_HANDLES
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.emissions_file_path = self.temp_path / "emissions.csv"

        # Create a mock SDK instance
        self.mock_sdk = Mock()

        # Create a mock response object that tests can configure
        self.mock_response = Mock()

        # Set default response so response.carbon_captured is True
        self.mock_response.carbon_captured = 1

        # Configure the capture_carbon method to return the mock response object
        self.mock_sdk.capture_carbon.return_value = self.mock_response

        # Patch the OneClickImpact class to return our mock
        patcher = patch("codecarbon.output_methods.offset.OneClickImpact")
        self.addCleanup(patcher.stop)
        self.mock_oneclick_impact = patcher.start()
        self.mock_oneclick_impact.return_value = self.mock_sdk

    def tearDown(self):
        fake_pynvml.INIT_MOCK.reset_mock()
        self.temp_dir.cleanup()

    def test_oneclick_output_initialization(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test OneClickImpactOutput initialization"""
        # Test initialization with default parameters
        output = OneClickImpactOutput(
            api_key=TEST_API_KEY,
            environment="sandbox",
            offset_threshold=1,
            auto_offset=True,
        )

        self.assertEqual(output.api_key, TEST_API_KEY)
        self.assertEqual(output.environment, "sandbox")
        self.assertEqual(output.offset_threshold, 1)
        self.assertEqual(output.auto_offset, True)
        self.assertEqual(output.accumulated_emissions_kg, 0.0)

    def test_kg_to_lbs_conversion(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test kg to lbs conversion with rounding"""

        output = OneClickImpactOutput(api_key=TEST_API_KEY)

        # Test conversion: 1 kg = 2.20462 lbs, rounded to 2 lbs
        self.assertEqual(output._kg_to_lbs(1.0), 2)
        # Test conversion: 0.5 kg = 1.10231 lbs, rounded to 1 lb
        self.assertEqual(output._kg_to_lbs(0.5), 1)
        # Test conversion: 2.5 kg = 5.51155 lbs, rounded to 6 lbs
        self.assertEqual(output._kg_to_lbs(2.5), 6)

    def test_threshold_validation(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test threshold validation and correction"""

        # Test threshold below minimum gets corrected to 0.5
        output = OneClickImpactOutput(api_key=TEST_API_KEY, offset_threshold=0)
        self.assertEqual(output.offset_threshold, 0.5)

        # Test valid threshold is preserved
        output = OneClickImpactOutput(api_key=TEST_API_KEY, offset_threshold=3)
        self.assertEqual(output.offset_threshold, 3)

    def test_offset_emissions(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test offset emissions functionality"""
        output = OneClickImpactOutput(api_key=TEST_API_KEY)

        # Test successful offset with 1 kg CO2
        result = output._offset_emissions(1.0)  # 1 kg CO2

        self.assertTrue(result)
        self.mock_sdk.capture_carbon.assert_called_once()

        # Check that the call was made with rounded lbs (1.0 kg * 2.20462 = 2 lbs rounded)
        call_args = self.mock_sdk.capture_carbon.call_args[1]
        expected_lbs = round(1.0 * 2.20462)  # Should be 2 lbs
        self.assertEqual(call_args["amount"], expected_lbs)
        self.assertEqual(output.accumulated_emissions_kg, 0.0)  # Reset after offset

    def test_offset_emissions_error_handling(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test error handling in offset emissions"""
        # Configure the mock SDK to raise an exception
        self.mock_sdk.capture_carbon.side_effect = Exception("API Error")

        output = OneClickImpactOutput(api_key=TEST_API_KEY)

        # Test failed offset
        result = output._offset_emissions(0.001)

        self.assertFalse(result)

    @patch("requests.get")
    def test_threshold_based_offsetting(
        self,
        mock_requests_get,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test threshold-based offsetting logic"""
        # Mock geography request
        mock_requests_get.return_value.json.return_value = GEO_METADATA_CANADA
        mock_requests_get.return_value.status_code = 200

        output = OneClickImpactOutput(
            api_key=TEST_API_KEY, offset_threshold=2, auto_offset=True  # 2kg threshold
        )

        # Create mock emissions data
        emissions_data = EmissionsData(
            timestamp="2023-01-01T00:00:00",
            project_name="test",
            run_id="test_run",
            experiment_id="test_exp",
            duration=100.0,
            emissions=1.0,  # 1 kg CO2 - below 2kg threshold
            emissions_rate=0.05,
            cpu_power=10.0,
            gpu_power=0.0,
            ram_power=2.0,
            cpu_energy=0.1,
            gpu_energy=0.0,
            ram_energy=0.02,
            energy_consumed=0.12,
            country_name="USA",
            country_iso_code="USA",
            region="California",
            cloud_provider="",
            cloud_region="",
            os="Linux",
            python_version="3.8",
            codecarbon_version="2.0.0",
            cpu_count=4.0,
            cpu_model="Intel i7",
            gpu_count=0.0,
            gpu_model="",
            longitude=-122.4194,
            latitude=37.7749,
            ram_total_size=16.0,
            tracking_mode="machine",
        )

        # First call - should not trigger offset (below threshold)
        output.out(emissions_data, emissions_data)
        self.mock_sdk.capture_carbon.assert_not_called()
        self.assertEqual(output.accumulated_emissions_kg, 1.0)

        # Second call - should trigger offset (exceeds threshold)
        emissions_data.emissions = 1.5  # Additional 1.5 kg CO2, total 2.5 kg
        output.out(emissions_data, emissions_data)

        # Should have been called once with accumulated emissions (2.5 kg total)
        self.mock_sdk.capture_carbon.assert_called_once()
        self.assertEqual(output.accumulated_emissions_kg, 0.0)  # Reset after offset

    def test_manual_offset(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test manual offset functionality"""

        output = OneClickImpactOutput(
            api_key=TEST_API_KEY, auto_offset=False  # Disable auto offset
        )

        # Accumulate some emissions manually
        output.accumulated_emissions_kg = 2.5  # Use higher value to ensure offset

        # Test manual offset
        result = output.manual_offset()

        self.assertTrue(result)
        self.mock_sdk.capture_carbon.assert_called_once()
        self.assertEqual(output.accumulated_emissions_kg, 0.0)

    @patch("requests.get")
    def test_tracker_integration(
        self,
        mock_requests_get,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test integration with EmissionsTracker"""
        # Mock geography request
        mock_requests_get.return_value.json.return_value = GEO_METADATA_CANADA
        mock_requests_get.return_value.status_code = 200

        # Test that tracker initializes OneClickImpact when API key is provided
        tracker = EmissionsTracker(
            project_name="test_project",
            output_dir=self.temp_path,
            output_file="test_emissions.csv",
            offset_api_key=TEST_API_KEY,
            offset_environment="sandbox",
            auto_offset=True,
            measure_power_secs=1,
            save_to_file=False,  # Prevent file creation in test
        )

        # Check that OneClickImpactOutput was added to output handlers
        oneclick_handlers = [
            handler
            for handler in tracker._output_handlers
            if isinstance(handler, OneClickImpactOutput)
        ]
        self.assertEqual(len(oneclick_handlers), 1)

        oneclick_handler = oneclick_handlers[0]
        self.assertEqual(oneclick_handler.api_key, TEST_API_KEY)
        self.assertEqual(oneclick_handler.environment, "sandbox")

    def test_import_error_handling(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test graceful handling when makeimpact is not installed"""
        # Import the offset module to access MAKEIMPACT_AVAILABLE
        from codecarbon.output_methods import offset

        # Save the original state
        original_available = offset.MAKEIMPACT_AVAILABLE

        try:
            # Simulate makeimpact not being available
            offset.MAKEIMPACT_AVAILABLE = False

            # Now creating OneClickImpactOutput should raise ImportError
            with self.assertRaises(ImportError) as context:
                OneClickImpactOutput(api_key=TEST_API_KEY)

            # Verify the error message
            self.assertIn("makeimpact package is required", str(context.exception))

        finally:
            # Restore the original state
            offset.MAKEIMPACT_AVAILABLE = original_available

    @patch("requests.get")
    def test_decorator_integration(
        self,
        mock_requests_get,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test integration with @track_emissions decorator"""
        # Mock geography request
        mock_requests_get.return_value.json.return_value = GEO_METADATA_CANADA
        mock_requests_get.return_value.status_code = 200

        @track_emissions(
            project_name="decorator_test",
            output_dir=self.temp_path,
            offset_api_key=TEST_API_KEY,
            auto_offset=True,
            save_to_file=False,  # Prevent file creation in test
        )
        def test_function():
            return "test_result"

        result = test_function()
        self.assertEqual(result, "test_result")

    def test_multiple_emissions_accumulation(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test that emissions accumulate correctly over multiple calls"""

        output = OneClickImpactOutput(
            api_key=TEST_API_KEY,
            offset_threshold=5,
            auto_offset=True,  # Higher threshold
        )

        # Create mock emissions data
        emissions_data = EmissionsData(
            timestamp="2023-01-01T00:00:00",
            project_name="test",
            run_id="test_run",
            experiment_id="test_exp",
            duration=100.0,
            emissions=1.5,  # 1.5 kg CO2
            emissions_rate=0.05,
            cpu_power=10.0,
            gpu_power=0.0,
            ram_power=2.0,
            cpu_energy=0.1,
            gpu_energy=0.0,
            ram_energy=0.02,
            energy_consumed=0.12,
            country_name="USA",
            country_iso_code="USA",
            region="California",
            cloud_provider="",
            cloud_region="",
            os="Linux",
            python_version="3.8",
            codecarbon_version="2.0.0",
            cpu_count=4.0,
            cpu_model="Intel i7",
            gpu_count=0.0,
            gpu_model="",
            longitude=-122.4194,
            latitude=37.7749,
            ram_total_size=16.0,
            tracking_mode="machine",
        )

        # First call - should accumulate but not trigger offset
        output.out(emissions_data, emissions_data)
        self.assertEqual(output.accumulated_emissions_kg, 1.5)
        self.mock_sdk.capture_carbon.assert_not_called()

        # Second call - should accumulate but still not trigger offset
        emissions_data.emissions = 2.0  # Additional 2.0 kg CO2, total 3.5 kg
        output.out(emissions_data, emissions_data)
        self.assertEqual(output.accumulated_emissions_kg, 3.5)
        self.mock_sdk.capture_carbon.assert_not_called()

        # Third call - should trigger offset (exceeds 5kg threshold)
        emissions_data.emissions = 2.0  # Additional 2.0 kg CO2, total 5.5 kg
        output.out(emissions_data, emissions_data)

        # Should have been called once with accumulated emissions (5.5 kg total)
        self.mock_sdk.capture_carbon.assert_called_once()
        self.assertEqual(output.accumulated_emissions_kg, 0.0)  # Reset after offset

    def test_auto_offset_disabled(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test that auto offset can be disabled"""

        output = OneClickImpactOutput(
            api_key=TEST_API_KEY,
            offset_threshold=0.5,  # Low threshold
            auto_offset=False,  # Disabled
        )

        # Create mock emissions data
        emissions_data = EmissionsData(
            timestamp="2023-01-01T00:00:00",
            project_name="test",
            run_id="test_run",
            experiment_id="test_exp",
            duration=100.0,
            emissions=5.0,  # 5 kg CO2 - well above threshold
            emissions_rate=0.05,
            cpu_power=10.0,
            gpu_power=0.0,
            ram_power=2.0,
            cpu_energy=0.1,
            gpu_energy=0.0,
            ram_energy=0.02,
            energy_consumed=0.12,
            country_name="USA",
            country_iso_code="USA",
            region="California",
            cloud_provider="",
            cloud_region="",
            os="Linux",
            python_version="3.8",
            codecarbon_version="2.0.0",
            cpu_count=4.0,
            cpu_model="Intel i7",
            gpu_count=0.0,
            gpu_model="",
            longitude=-122.4194,
            latitude=37.7749,
            ram_total_size=16.0,
            tracking_mode="machine",
        )

        # Should not trigger offset even though above threshold because auto_offset=False
        # But emissions should still accumulate for potential manual offset later
        output.out(emissions_data, emissions_data)
        self.assertEqual(
            output.accumulated_emissions_kg, 5.0
        )  # Emissions should accumulate
        self.mock_sdk.capture_carbon.assert_not_called()

    def test_environment_configuration(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test different environment configurations"""

        # Test sandbox environment
        output_sandbox = OneClickImpactOutput(
            api_key=TEST_API_KEY, environment="sandbox"
        )
        self.assertEqual(output_sandbox.environment, "sandbox")

        # Test production environment
        output_production = OneClickImpactOutput(
            api_key=TEST_API_KEY, environment="production"
        )
        self.assertEqual(output_production.environment, "production")

    def test_edge_case_very_small_emissions(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test handling of very small emission values - should not call capture_carbon for < 1 lb"""

        output = OneClickImpactOutput(api_key=TEST_API_KEY)

        # Test very small emission value (0.0001 kg = 0.1 g)
        # This converts to 0 lbs when rounded: round(0.0001 * 2.20462) = round(0.00022) = 0
        # Should not call capture_carbon for amounts less than 1 lb
        result = output._offset_emissions(0.0001)

        # Should return False because amount is less than 1 lb
        self.assertFalse(result)
        # Should not call capture_carbon with less than 1 lb
        self.mock_sdk.capture_carbon.assert_not_called()

    def test_minimum_offset_threshold(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test that offset only happens when converted amount is at least 1 lb"""

        output = OneClickImpactOutput(api_key=TEST_API_KEY)

        # Test with amount that converts to exactly 1 lb
        # 1 lb = 0.453592 kg, so we need slightly more than that to round to 1 lb
        # 0.45 kg * 2.20462 = 0.992079 ≈ 1 lb when rounded
        result_below_1lb = output._offset_emissions(0.45)  # Should round to 1 lb
        self.assertTrue(result_below_1lb)
        self.mock_sdk.capture_carbon.assert_called_once()

        # Verify it was called with 1 lb
        call_args = self.mock_sdk.capture_carbon.call_args[1]
        self.assertEqual(call_args["amount"], 1)

        # Reset mock for next test
        self.mock_sdk.reset_mock()

        # Test with amount that converts to less than 1 lb
        result_below_1lb = output._offset_emissions(
            0.22
        )  # 0.22 kg * 2.20462 = 0.485 ≈ 0 lbs when rounded
        self.assertFalse(result_below_1lb)
        self.mock_sdk.capture_carbon.assert_not_called()

    def test_accumulation_with_small_emissions(
        self,
        mock_setup_intel_cli,
        mock_log_values,
        mocked_get_gpu_details,
        mocked_env_cloud_details,
        mocked_is_gpu_details_available,
    ):
        """Test that small emissions accumulate even if individual amounts are below 1 lb threshold"""

        output = OneClickImpactOutput(
            api_key=TEST_API_KEY, offset_threshold=2, auto_offset=True  # 2 kg threshold
        )

        # Create emissions data with small amount (below 2 kg)
        emissions_data = EmissionsData(
            timestamp="2023-01-01T00:00:00",
            project_name="test",
            run_id="test_run",
            experiment_id="test_exp",
            duration=100.0,
            emissions=0.3,  # 0.3 kg - converts to ~0.66 lbs, rounds to 1 lb but below threshold
            emissions_rate=0.05,
            cpu_power=10.0,
            gpu_power=0.0,
            ram_power=2.0,
            cpu_energy=0.1,
            gpu_energy=0.0,
            ram_energy=0.02,
            energy_consumed=0.12,
            country_name="USA",
            country_iso_code="USA",
            region="California",
            cloud_provider="",
            cloud_region="",
            os="Linux",
            python_version="3.8",
            codecarbon_version="2.0.0",
            cpu_count=4.0,
            cpu_model="Intel i7",
            gpu_count=0.0,
            gpu_model="",
            longitude=-122.4194,
            latitude=37.7749,
            ram_total_size=16.0,
            tracking_mode="machine",
        )

        # First call - should accumulate but not trigger offset
        output.out(emissions_data, emissions_data)
        self.assertEqual(output.accumulated_emissions_kg, 0.3)
        self.mock_sdk.capture_carbon.assert_not_called()

        # Second call - should accumulate and trigger offset (above threshold)
        emissions_data.emissions = 0.8  # Additional 0.8 kg, total 1.1 kg
        output.out(emissions_data, emissions_data)
        self.assertEqual(output.accumulated_emissions_kg, 1.1)

        # Should not call capture_carbon yet because 1.1 kg is still below 2 kg threshold
        self.mock_sdk.capture_carbon.assert_not_called()

        # Third call - should trigger offset (exceeds 2 kg threshold)
        emissions_data.emissions = 1.0  # Additional 1.0 kg, total 2.1 kg
        output.out(emissions_data, emissions_data)
        self.assertEqual(output.accumulated_emissions_kg, 0.0)
        # Should have been called once with accumulated emissions (2.1 kg = ~4.63 lbs = 5 lbs rounded)
        self.mock_sdk.capture_carbon.assert_called_once()
        call_args = self.mock_sdk.capture_carbon.call_args[1]
        expected_lbs = round(2.1 * 2.20462)  # Should be 5 lbs
        self.assertEqual(call_args["amount"], expected_lbs)


if __name__ == "__main__":
    unittest.main()
