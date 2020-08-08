import unittest

from co2_tracker.emissions import get_private_infra_emissions, get_cloud_emissions
from co2_tracker.units import Energy
from co2_tracker.external import CloudMetadata, GeoMetadata
from tests.testutils import get_test_app_config


class TestEmissions(unittest.TestCase):
    def setUp(self) -> None:
        # GIVEN
        self.app_config = get_test_app_config()

    def test_get_emissions_CLOUD_AWS(self):
        # WHEN

        emissions = get_cloud_emissions(
            Energy.from_energy(kwh=0.6),
            CloudMetadata(provider="aws", region="us-east-1"),
            self.app_config,
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.22, places=2)

    def test_emissions_CLOUD_AZURE(self):
        # WHEN
        emissions = get_cloud_emissions(
            Energy.from_energy(kwh=1.5),
            CloudMetadata(provider="azure", region="eastus"),
            self.app_config,
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.55, places=2)

    def test_emissions_CLOUD_GCP(self):
        emissions = get_cloud_emissions(
            Energy.from_energy(kwh=0.01),
            CloudMetadata(provider="gcp", region="us-central1"),
            self.app_config,
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.01, places=2)

    def test_get_emissions_PRIVATE_INFRA_USA_WITH_REGION(self):
        # WHEN
        emissions = get_private_infra_emissions(
            Energy.from_energy(kwh=0.3),
            GeoMetadata(country="United States", region="Illinois"),
            self.app_config,
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.11, places=2)

    def test_get_emissions_PRIVATE_INFRA_USA_WITHOUT_REGION(self):
        # WHEN
        emissions = get_private_infra_emissions(
            Energy.from_energy(kwh=0.3),
            GeoMetadata(country="United States"),
            self.app_config,
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.20, places=2)

    def test_get_emissions_PRIVATE_INFRA_CANADA(self):

        # WHEN
        emissions = get_private_infra_emissions(
            Energy.from_energy(kwh=3), GeoMetadata(country="Canada"), self.app_config
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 1.6, places=2)
