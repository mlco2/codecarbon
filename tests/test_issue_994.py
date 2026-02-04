import unittest
from unittest.mock import MagicMock, patch

from codecarbon.core.units import Energy, Power
from codecarbon.emissions_tracker import EmissionsTracker


class TestIssue994(unittest.TestCase):
    @patch("codecarbon.emissions_tracker.EmissionsTracker._get_geo_metadata")
    @patch("codecarbon.emissions_tracker.EmissionsTracker._get_cloud_metadata")
    @patch("codecarbon.core.electricitymaps_api.requests.get")
    @patch("codecarbon.emissions_tracker.ResourceTracker")
    @patch("codecarbon.emissions_tracker.BaseEmissionsTracker.get_detected_hardware")
    @patch("codecarbon.emissions_tracker.PeriodicScheduler")
    def test_cumulative_emissions_with_varying_intensity(
        self,
        mock_scheduler,
        mock_get_hw,
        mock_resource_tracker,
        mock_get,
        mock_cloud,
        mock_geo,
    ):
        # Setup mocks
        mock_geo.return_value = MagicMock(
            latitude=1.0,
            longitude=1.0,
            country_iso_code="USA",
            country_2letter_iso_code="US",
        )
        mock_cloud.return_value = MagicMock(
            is_on_private_infra=True, provider="azure", region="eastus"
        )
        mock_get_hw.return_value = {
            "ram_total_size": 16.0,
            "cpu_count": 8,
            "cpu_physical_count": 4,
            "cpu_model": "Mock CPU",
            "gpu_count": 0,
            "gpu_model": "None",
            "gpu_ids": None,
        }

        # Mock Electricity Maps API responses with different intensities
        # 1st call: 100 g/kWh, 2nd call: 200 g/kWh, 3rd call: 300 g/kWh
        responses = [
            MagicMock(status_code=200, json=lambda: {"carbonIntensity": 100}),
            MagicMock(status_code=200, json=lambda: {"carbonIntensity": 200}),
            MagicMock(status_code=200, json=lambda: {"carbonIntensity": 300}),
        ]
        mock_get.side_effect = responses

        tracker = EmissionsTracker(
            electricitymaps_api_token="test-token",
            save_to_file=False,
            measure_power_secs=1,
            allow_multiple_runs=True,
        )

        # Manually inject a mock hardware component
        mock_cpu = MagicMock()
        from codecarbon.external.hardware import CPU

        mock_cpu.__class__ = CPU
        # Mock measure_power_and_energy: return 1kWh delta each time
        mock_cpu.measure_power_and_energy.return_value = (
            Power.from_watts(100),
            Energy.from_energy(kWh=1.0),
        )
        tracker._hardware = [mock_cpu]

        # Start tracking
        tracker.start()

        # Step 1
        tracker._measure_power_and_energy()
        # total_energy = 1.0, intensity = 100 => emissions = 0.1 kg
        data1 = tracker._prepare_emissions_data()
        self.assertAlmostEqual(data1.emissions, 0.1)

        # Step 2
        tracker._measure_power_and_energy()
        # total_energy = 2.0, delta_energy = 1.0, intensity = 200 => delta_emissions = 0.2 kg
        # total_emissions = 0.1 + 0.2 = 0.3 kg
        data2 = tracker._prepare_emissions_data()
        self.assertAlmostEqual(data2.emissions, 0.3)

        # Step 3
        tracker._measure_power_and_energy()
        # total_energy = 3.0, delta_energy = 1.0, intensity = 300 => delta_emissions = 0.3 kg
        # total_emissions = 0.3 + 0.3 = 0.6 kg
        data3 = tracker._prepare_emissions_data()
        self.assertAlmostEqual(data3.emissions, 0.6)

        # Verification: If it wasn't cumulative, it would be 3.0 kWh * 300 g/kWh = 0.9 kg
        self.assertLess(data3.emissions, 0.8)


if __name__ == "__main__":
    unittest.main()
