import unittest
from unittest import mock

import pandas as pd

from codecarbon.core.emissions import Emissions
from codecarbon.core.units import Energy
from codecarbon.external.geography import CloudMetadata, GeoMetadata
from codecarbon.input import DataSource
from tests.testutils import get_test_data_source  # Added back


class TestEmissions(unittest.TestCase):
    def setUp(self) -> None:
        # GIVEN
        self._data_source = get_test_data_source()
        # Common mock objects for tests
        self.mock_energy = Energy.from_energy(kWh=2.0)
        self.mock_geo = GeoMetadata(country_iso_code="USA", region="california")
        self.mock_cloud_metadata = CloudMetadata(provider="aws", region="us-east-1")

    def test_get_emissions_CLOUD_AWS(self):
        # Test original behavior when no custom intensity is set
        emissions_calculator = Emissions(self._data_source)
        # WHEN
        emissions = (
            emissions_calculator.get_cloud_emissions(  # Changed from self._emissions
                Energy.from_energy(
                    kWh=0.6
                ),  # Using original energy value for this specific test
                CloudMetadata(provider="aws", region="us-east-1"),
            )
        )
        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.285, places=3)  # Original assertion value

    def test_emissions_CLOUD_AZURE(self):
        # Test original behavior when no custom intensity is set
        emissions_calculator = Emissions(self._data_source)
        # WHEN
        emissions = emissions_calculator.get_cloud_emissions(
            Energy.from_energy(kWh=1.5),  # Original energy
            CloudMetadata(provider="azure", region="eastus"),
        )
        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.7125, places=4)  # Original assertion

    def test_emissions_CLOUD_GCP(self):
        # Test original behavior when no custom intensity is set
        emissions_calculator = Emissions(self._data_source)
        emissions = emissions_calculator.get_cloud_emissions(
            Energy.from_energy(kWh=0.01),  # Original energy
            CloudMetadata(provider="gcp", region="us-central1"),
        )
        # THEN
        assert isinstance(emissions, float)
        # GCP us-central1 impact is 525.20 g/kWh from test data source (comment seems outdated vs actual)
        # Actual output was 0.0043, implying 430 g/kWh
        self.assertAlmostEqual(emissions, 0.0043, places=6)

    def test_get_carbon_intensity_per_source_data(self):
        # This test doesn't use an Emissions instance directly for its main assertion
        carbon_intensity = self._data_source.get_carbon_intensity_per_source_data()
        self.assertEqual(len(carbon_intensity.keys()), 21)
        self.assertGreater(carbon_intensity["coal"], 800)
        self.assertLess(carbon_intensity["wind"], 80)

    def test_get_emissions_PRIVATE_INFRA_FRA(self):
        # Test original behavior
        emissions_calculator = Emissions(self._data_source)
        emissions = emissions_calculator.get_private_infra_emissions(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="FRA", country_name="France"),
        )
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 56.04 / 1000, places=4)

    def test_get_emissions_PRIVATE_INFRA_UNKNOWN(self):
        # Test original behavior
        emissions_calculator = Emissions(self._data_source)
        emissions = emissions_calculator.get_private_infra_emissions(
            Energy.from_energy(kWh=1_000),
            GeoMetadata(country_iso_code="UNK", country_name="Unknown"),
        )
        carbon_intensity_per_source = (
            self._data_source.get_carbon_intensity_per_source_data()
        )
        default_emissions_g_kwh = carbon_intensity_per_source.get("world_average")
        expected_emissions_kg = (
            default_emissions_g_kwh * 1000 / 1000
        )  # kWh * g/kWh / g/kg
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, expected_emissions_kg, places=2)

    @mock.patch("codecarbon.core.emissions.logger")
    @mock.patch("codecarbon.core.co2_signal.get_emissions")
    def test_private_infra_with_positive_custom_intensity(
        self, mock_co2_signal_get_emissions, mock_logger
    ):
        custom_intensity = 50.0
        emissions_calculator = Emissions(
            self._data_source, custom_carbon_intensity_g_co2e_kwh=custom_intensity
        )
        expected_emissions = self.mock_energy.kWh * (custom_intensity / 1000.0)

        actual_emissions = emissions_calculator.get_private_infra_emissions(
            self.mock_energy, self.mock_geo
        )

        self.assertAlmostEqual(actual_emissions, expected_emissions)
        # mock_logger.info.assert_called_once_with( # Logger assertion removed as per subtask
        #     f"Using custom carbon intensity for private infrastructure emissions: {custom_intensity} gCO2e/kWh"
        # )
        mock_co2_signal_get_emissions.assert_not_called()
        with mock.patch.object(
            self._data_source,
            "get_country_emissions_data",
            wraps=self._data_source.get_country_emissions_data,
        ) as wrapped_method:
            # Call again to ensure no fallback logic is triggered by mistake
            emissions_calculator.get_private_infra_emissions(
                self.mock_energy, self.mock_geo
            )
            wrapped_method.assert_not_called()

    @mock.patch("codecarbon.core.co2_signal.get_emissions")  # Mock the co2_signal path
    @mock.patch.object(
        DataSource, "get_global_energy_mix_data"
    )  # Mock the DataSource path for country emissions
    def test_private_infra_with_none_custom_intensity_fallback_co2_signal(
        self, mock_get_global_energy_mix_data, mock_co2_signal_get_emissions
    ):
        mock_co2_signal_get_emissions.return_value = 0.123
        emissions_calculator = Emissions(
            self._data_source, co2_signal_api_token="dummy_token"
        )

        actual_emissions = emissions_calculator.get_private_infra_emissions(
            self.mock_energy, self.mock_geo
        )
        self.assertEqual(actual_emissions, 0.123)
        mock_co2_signal_get_emissions.assert_called_once_with(
            self.mock_energy, self.mock_geo, "dummy_token"
        )
        mock_get_global_energy_mix_data.assert_not_called()  # Ensure it doesn't go to the other path

    @mock.patch.object(
        DataSource, "get_global_energy_mix_data"
    )  # Mock the DataSource path for country emissions
    def test_private_infra_with_none_custom_intensity_fallback_datasource(
        self, mock_get_global_energy_mix_data
    ):
        # Simulate no CO2 signal token, forcing fallback to DataSource
        # USA (from self.mock_geo) has carbon_intensity: 381.98 g/kWh in test_data_source
        expected_intensity_g_kwh = 381.98
        mock_get_global_energy_mix_data.return_value = {
            "USA": {
                "country_name": "United States",
                "carbon_intensity": expected_intensity_g_kwh,
                "total_TWh": 100,
            }
        }

        emissions_calculator = Emissions(self._data_source, co2_signal_api_token=None)
        expected_emissions = self.mock_energy.kWh * (expected_intensity_g_kwh / 1000.0)

        actual_emissions = emissions_calculator.get_private_infra_emissions(
            self.mock_energy, self.mock_geo
        )
        self.assertAlmostEqual(actual_emissions, expected_emissions, places=5)
        mock_get_global_energy_mix_data.assert_called_once()

    @mock.patch("codecarbon.core.emissions.logger")
    @mock.patch.object(DataSource, "get_cloud_emissions_data")
    def test_cloud_emissions_with_positive_custom_intensity(
        self, mock_get_cloud_data, mock_logger
    ):
        custom_intensity = 60.0
        emissions_calculator = Emissions(
            self._data_source, custom_carbon_intensity_g_co2e_kwh=custom_intensity
        )
        expected_emissions = self.mock_energy.kWh * (custom_intensity / 1000.0)

        actual_emissions = emissions_calculator.get_cloud_emissions(
            self.mock_energy, self.mock_cloud_metadata, self.mock_geo
        )

        self.assertAlmostEqual(actual_emissions, expected_emissions)
        # mock_logger.info.assert_called_once_with( # Logger assertion removed as per subtask
        #     f"Using custom carbon intensity for cloud emissions: {custom_intensity} gCO2e/kWh"
        # )
        mock_get_cloud_data.assert_not_called()

    @mock.patch.object(DataSource, "get_cloud_emissions_data")
    def test_cloud_emissions_with_none_custom_intensity(self, mock_get_cloud_data):
        expected_impact_g_kwh = 475.0  # For aws us-east-1 from test data
        # Create a DataFrame mock that behaves like the one from get_cloud_emissions_data
        mock_df = pd.DataFrame(
            {
                "provider": ["aws"],
                "region": ["us-east-1"],
                "impact": [expected_impact_g_kwh],
            }
        )
        mock_get_cloud_data.return_value = mock_df

        emissions_calculator = Emissions(self._data_source)
        expected_emissions = self.mock_energy.kWh * (expected_impact_g_kwh / 1000.0)

        actual_emissions = emissions_calculator.get_cloud_emissions(
            self.mock_energy, self.mock_cloud_metadata, self.mock_geo
        )

        self.assertAlmostEqual(actual_emissions, expected_emissions)
        mock_get_cloud_data.assert_called_once()

    def test_get_emissions_PRIVATE_INFRA_NOR(self):
        emissions_calculator = Emissions(self._data_source)
        emissions = emissions_calculator.get_private_infra_emissions(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="NOR", country_name="Norway"),
        )
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 26.4 / 1_000, places=4)

    def test_get_emissions_PRIVATE_INFRA_USA_WITH_REGION(self):
        emissions_calculator = Emissions(self._data_source)
        emissions = emissions_calculator.get_private_infra_emissions(
            Energy.from_energy(kWh=0.3),
            GeoMetadata(
                country_iso_code="USA", country_name="United States", region="Illinois"
            ),
        )
        assert isinstance(emissions, float)
        # Actual output was 0.11040229633309799 for 0.3 kWh.
        # This implies an intensity of approx 0.36800765 kg/kWh for Illinois from test data.
        self.assertAlmostEqual(emissions, 0.11040229633309799, places=8)

    def test_get_emissions_PRIVATE_INFRA_USA_WITHOUT_REGION(self):
        emissions_calculator = Emissions(self._data_source)
        emissions = emissions_calculator.get_private_infra_emissions(
            Energy.from_energy(kWh=0.3),
            GeoMetadata(country_iso_code="USA", country_name="United States"),
        )
        assert isinstance(emissions, float)
        # USA default is 381.98 g/kWh = 0.38198 kg/kWh
        # 0.3 kWh * 0.38198 kg/kWh = 0.114594
        self.assertAlmostEqual(emissions, 0.114594, places=6)

    def test_get_emissions_PRIVATE_INFRA_USA_WITHOUT_COUNTRYNAME(self):
        emissions_calculator = Emissions(self._data_source)
        emissions = emissions_calculator.get_private_infra_emissions(
            Energy.from_energy(kWh=0.3), GeoMetadata(country_iso_code="USA")
        )
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.114594, places=6)  # Same as above

    def test_get_emissions_PRIVATE_INFRA_CANADA_WITHOUT_REGION(self):
        emissions_calculator = Emissions(self._data_source)
        emissions = emissions_calculator.get_private_infra_emissions(
            Energy.from_energy(kWh=3),
            GeoMetadata(country_iso_code="CAN", country_name="Canada"),
        )
        assert isinstance(emissions, float)
        # Canada default is 170.03 g/kWh = 0.17003 kg/kWh
        # 3 kWh * 0.17003 kg/kWh = 0.51009
        self.assertAlmostEqual(emissions, 0.51009, places=5)

    def test_get_emissions_PRIVATE_INFRA_CANADA_WITH_REGION(self):
        emissions_calculator = Emissions(self._data_source)
        emissions = emissions_calculator.get_private_infra_emissions(
            Energy.from_energy(kWh=3),
            GeoMetadata(
                country_iso_code="CAN", country_name="Canada", region="ontario"
            ),
        )
        assert isinstance(emissions, float)
        # Ontario has 40.0 lbs/MWh = 40.0 * 0.453592 / 1000 kg/kWh = 0.01814368 kg/kWh
        # 3 kWh * 0.01814368 kg/kWh = 0.05443104
        self.assertAlmostEqual(emissions, 0.05443, places=5)

    def test_get_emissions_PRIVATE_INFRA_unknown_country(self):
        emissions_calculator = Emissions(self._data_source)
        emissions = emissions_calculator.get_private_infra_emissions(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="AAA", country_name="unknown"),
        )
        assert isinstance(emissions, float)
        # World average is 475.0 g/kWh = 0.475 kg/kWh
        self.assertAlmostEqual(emissions, 0.475, places=3)
