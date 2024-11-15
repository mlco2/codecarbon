import unittest

from codecarbon.core.emissions import Emissions
from codecarbon.core.units import Energy
from codecarbon.external.geography import CloudMetadata, GeoMetadata
from codecarbon.input import DataSource
from tests.testutils import get_test_data_source


class TestEmissions(unittest.TestCase):
    def setUp(self) -> None:
        # GIVEN
        self._data_source = get_test_data_source()
        self._emissions = Emissions(self._data_source)

    def test_get_emissions_CLOUD_AWS(self):
        # WHEN

        emissions = self._emissions.get_cloud_emissions(
            Energy.from_energy(kWh=0.6),
            CloudMetadata(provider="aws", region="us-east-1"),
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.285, places=2)

    def test_emissions_CLOUD_AZURE(self):
        # WHEN
        emissions = self._emissions.get_cloud_emissions(
            Energy.from_energy(kWh=1.5),
            CloudMetadata(provider="azure", region="eastus"),
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.7125, places=2)

    def test_emissions_CLOUD_GCP(self):
        emissions = self._emissions.get_cloud_emissions(
            Energy.from_energy(kWh=0.01),
            CloudMetadata(provider="gcp", region="us-central1"),
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.0010, places=2)

    def test_get_carbon_intensity_per_source_data(self):
        # pytest tests/test_emissions.py::TestEmissions::test_get_carbon_intensity_per_source_data
        carbon_intensity = DataSource().get_carbon_intensity_per_source_data()
        self.assertEqual(len(carbon_intensity.keys()), 21)
        self.assertGreater(carbon_intensity["coal"], 800)
        self.assertLess(carbon_intensity["wind"], 80)

    def test_get_emissions_PRIVATE_INFRA_FRA(self):
        """
        European country is a specific case as we have there carbon intensity to
        without computation.
        """
        # WHEN
        emissions = self._emissions.get_private_infra_emissions(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="FRA", country_name="France"),
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 56.04 / 1000, places=2)

    def test_get_emissions_PRIVATE_INFRA_UNKNOWN(self):
        """
        Test with a country that is not in the list of known countries.
        """
        # WHEN

        emissions = self._emissions.get_private_infra_emissions(
            Energy.from_energy(kWh=1_000),
            GeoMetadata(country_iso_code="UNK", country_name="Unknown"),
        )

        # THEN
        carbon_intensity_per_source = (
            DataSource().get_carbon_intensity_per_source_data()
        )
        default_emissions = carbon_intensity_per_source.get("world_average")
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, default_emissions, places=2)

    def test_get_emissions_PRIVATE_INFRA_NOR(self):
        """
        Norway utilises hydropower more than any other country around the globe
        """
        # WHEN
        emissions = self._emissions.get_private_infra_emissions(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="NOR", country_name="Norway"),
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 26.4 / 1_000, places=2)

    def test_get_emissions_PRIVATE_INFRA_USA_WITH_REGION(self):
        # WHEN
        emissions = self._emissions.get_private_infra_emissions(
            Energy.from_energy(kWh=0.3),
            GeoMetadata(
                country_iso_code="USA", country_name="United States", region="Illinois"
            ),
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.11, places=2)

    def test_get_emissions_PRIVATE_INFRA_USA_WITHOUT_REGION(self):
        # WHEN
        emissions = self._emissions.get_private_infra_emissions(
            Energy.from_energy(kWh=0.3),
            GeoMetadata(country_iso_code="USA", country_name="United States"),
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.115, places=2)

    def test_get_emissions_PRIVATE_INFRA_USA_WITHOUT_COUNTRYNAME(self):
        # WHEN
        emissions = self._emissions.get_private_infra_emissions(
            Energy.from_energy(kWh=0.3), GeoMetadata(country_iso_code="USA")
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.115, places=2)

    def test_get_emissions_PRIVATE_INFRA_CANADA_WITHOUT_REGION(self):
        # WHEN
        emissions = self._emissions.get_private_infra_emissions(
            Energy.from_energy(kWh=3),
            GeoMetadata(country_iso_code="CAN", country_name="Canada"),
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.5101, places=2)

    def test_get_emissions_PRIVATE_INFRA_CANADA_WITH_REGION(self):
        # WHEN
        emissions = self._emissions.get_private_infra_emissions(
            Energy.from_energy(kWh=3),
            GeoMetadata(
                country_iso_code="CAN", country_name="Canada", region="ontario"
            ),
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.12, places=2)

    def test_get_emissions_PRIVATE_INFRA_unknown_country(self):
        """
        If we do not know the country we fallback to a default value.
        """
        emissions = self._emissions.get_private_infra_emissions(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="AAA", country_name="unknown"),
        )
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.475, places=2)
