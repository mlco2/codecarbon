import unittest
from unittest.mock import patch

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
        self.assertEqual(len(carbon_intensity.keys()), 27)
        self.assertGreater(carbon_intensity["coal"], 800)
        self.assertLess(carbon_intensity["wind"], 80)

    def test_energy_mix_with_biomass_and_waste_is_not_dropped(self):
        """
        A mix carrying biomass and waste must be priced from the factor table.
        Without a factor for them, the two types are left out of the computed
        sum, the sanity check fails and the world average is returned (#1415).
        """
        # GIVEN
        factors = DataSource().get_carbon_intensity_per_source_data()
        energy_mix = {
            "total_TWh": 10.0,
            "hydroelectricity_TWh": 6.0,
            "biomass_TWh": 3.0,
            "waste_TWh": 1.0,
        }

        # WHEN
        rate = Emissions._global_energy_mix_to_emissions_rate(energy_mix)

        # THEN
        self.assertNotAlmostEqual(
            rate.kgs_per_kWh * 1000, factors["world_average"], places=6
        )
        expected = (
            6.0 * factors["hydroelectricity"]
            + 3.0 * factors["biomass"]
            + 1.0 * factors["waste"]
        ) / 10.0
        self.assertAlmostEqual(rate.kgs_per_kWh * 1000, expected, places=6)

    def test_energy_mix_with_biofuel_key_from_global_energy_mix(self):
        """
        global_energy_mix.json names bioenergy generation ``biofuel_TWh``, so
        the factor has to be reachable under that name as well.
        """
        # GIVEN
        factors = DataSource().get_carbon_intensity_per_source_data()
        energy_mix = {
            "total_TWh": 10.0,
            "hydroelectricity_TWh": 6.0,
            "biofuel_TWh": 4.0,
        }

        # WHEN
        rate = Emissions._global_energy_mix_to_emissions_rate(energy_mix)

        # THEN
        self.assertNotAlmostEqual(
            rate.kgs_per_kWh * 1000, factors["world_average"], places=6
        )
        expected = (6.0 * factors["hydroelectricity"] + 4.0 * factors["biomass"]) / 10.0
        self.assertEqual(factors["biofuel"], factors["biomass"])
        self.assertAlmostEqual(rate.kgs_per_kWh * 1000, expected, places=6)

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
        # Illinois: 474.4 lbCO2eq/MWh in eGRID2023
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.3 * 474.4 * 0.00045359237, places=4)

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
        manually_computed_emissions = (
            3 * (0.995725971 * 0.0 + 0.8166885263 * 0.1 + 0.7438415916 * 8.6) / 100.1
        )

        # THEN
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, manually_computed_emissions, places=2)

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

    def test_get_emissions_PRIVATE_INFRA_without_country_metadata(self):
        emissions = self._emissions.get_private_infra_emissions(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code=None, country_name=None, region=None),
        )

        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 0.475, places=2)

    @patch("codecarbon.core.electricitymaps_api.get_emissions")
    def test_private_infra_uses_forced_intensity_when_set(self, mocked_get_emissions):
        emissions_calculator = Emissions(
            self._data_source, force_carbon_intensity_g_co2e_kwh=50.0
        )

        emissions = emissions_calculator.get_private_infra_emissions(
            Energy.from_energy(kWh=2),
            GeoMetadata(country_iso_code="CAN", country_name="Canada"),
        )

        self.assertAlmostEqual(emissions, 0.1, places=6)
        mocked_get_emissions.assert_not_called()

    def test_cloud_uses_forced_intensity_when_set(self):
        emissions_calculator = Emissions(
            self._data_source, force_carbon_intensity_g_co2e_kwh=100.0
        )

        emissions = emissions_calculator.get_cloud_emissions(
            Energy.from_energy(kWh=2),
            CloudMetadata(provider="aws", region="us-east-1"),
        )

        self.assertAlmostEqual(emissions, 0.2, places=6)

    def test_get_emissions_PRIVATE_INFRA_NORDIC_REGION(self):
        # WHEN
        # Test Nordic region (Sweden SE2)

        emissions = self._emissions.get_private_infra_emissions(
            Energy.from_energy(kWh=1.0),
            GeoMetadata(country_iso_code="SWE", country_name="Sweden", region="SE2"),
        )

        # THEN
        # Nordic regions use static emission factors from the JSON file
        # SE2 has an emission factor specified in nordic_emissions.json
        nordic_data = self._data_source.get_nordic_country_energy_mix_data()
        emission_factor_g = nordic_data["data"]["SE2"]["emission_factor"]
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, emission_factor_g / 1000, places=6)

    def test_get_emissions_PRIVATE_INFRA_NORDIC_FINLAND(self):
        # WHEN
        # Test Nordic region (Finland)

        emissions = self._emissions.get_private_infra_emissions(
            Energy.from_energy(kWh=2.5),
            GeoMetadata(country_iso_code="FIN", country_name="Finland", region="FI"),
        )

        # THEN
        # Finland (FI) should use Nordic static emission factors
        assert isinstance(emissions, float)
        expected_emissions = 0.072 * 2.5
        self.assertAlmostEqual(emissions, expected_emissions, places=6)

    def test_get_emissions_PRIVATE_INFRA_NORDIC_REGION_uses_static_factor_without_token(
        self,
    ):
        # GIVEN
        energy = Energy.from_energy(kWh=1.0)
        geo = GeoMetadata(country_iso_code="SWE", country_name="Sweden", region="SE2")

        # WHEN
        emissions = self._emissions.get_private_infra_emissions(energy, geo)

        # THEN
        expected_country = self._emissions.get_country_emissions(energy, geo)
        nordic_data = self._data_source.get_nordic_country_energy_mix_data()
        emission_factor_g = nordic_data["data"]["SE2"]["emission_factor"]
        expected_nordic = (emission_factor_g / 1000) * energy.kWh
        self.assertAlmostEqual(emissions, expected_nordic, places=6)
        self.assertNotAlmostEqual(emissions, expected_country, places=4)

    def test_try_get_nordic_region_emissions_returns_none_without_region(self):
        # GIVEN
        energy = Energy.from_energy(kWh=1.0)
        geo = GeoMetadata(country_iso_code="SWE", country_name="Sweden", region=None)

        # WHEN
        emissions = self._emissions._try_get_nordic_region_emissions(energy, geo)

        # THEN
        self.assertIsNone(emissions)

    def test_try_get_nordic_region_emissions_returns_none_for_non_nordic_region(self):
        # GIVEN
        energy = Energy.from_energy(kWh=1.0)
        geo = GeoMetadata(country_iso_code="SWE", country_name="Sweden", region="XYZ")

        # WHEN
        emissions = self._emissions._try_get_nordic_region_emissions(energy, geo)

        # THEN
        self.assertIsNone(emissions)

    def test_nordic_admin_regions_fall_back_to_country_without_regional_lookup(self):
        energy = Energy.from_energy(kWh=1.0)
        admin_regions = [
            ("SWE", "Sweden", "Stockholm County"),
            ("NOR", "Norway", "Oslo"),
            ("FIN", "Finland", "Uusimaa"),
        ]

        for country_iso_code, country_name, region in admin_regions:
            with self.subTest(country_iso_code=country_iso_code, region=region):
                geo = GeoMetadata(
                    country_iso_code=country_iso_code,
                    country_name=country_name,
                    region=region,
                )
                expected_emissions = self._emissions.get_country_emissions(energy, geo)

                with (
                    patch.object(
                        self._data_source, "get_nordic_country_energy_mix_data"
                    ) as get_nordic_data,
                    patch.object(
                        self._data_source, "get_country_emissions_data"
                    ) as get_regional_emissions_data,
                    patch.object(
                        self._data_source, "get_country_energy_mix_data"
                    ) as get_regional_energy_mix_data,
                    patch("codecarbon.core.emissions.logger.error") as log_error,
                    patch("codecarbon.core.emissions.logger.warning") as log_warning,
                ):
                    emissions = self._emissions.get_private_infra_emissions(energy, geo)

                self.assertAlmostEqual(emissions, expected_emissions, places=6)
                get_nordic_data.assert_not_called()
                get_regional_emissions_data.assert_not_called()
                get_regional_energy_mix_data.assert_not_called()
                log_error.assert_not_called()
                log_warning.assert_not_called()

    def test_nordic_region_missing_static_data_falls_back_to_country(self):
        energy = Energy.from_energy(kWh=1.0)
        geo = GeoMetadata(country_iso_code="SWE", country_name="Sweden", region="SE2")
        expected_emissions = self._emissions.get_country_emissions(energy, geo)

        with (
            patch.object(
                self._data_source,
                "get_nordic_country_energy_mix_data",
                return_value={"data": {}},
            ),
            patch.object(
                self._data_source, "get_country_emissions_data"
            ) as get_regional_emissions_data,
            patch.object(
                self._data_source, "get_country_energy_mix_data"
            ) as get_regional_energy_mix_data,
        ):
            emissions = self._emissions.get_private_infra_emissions(energy, geo)

        self.assertAlmostEqual(emissions, expected_emissions, places=6)
        get_regional_emissions_data.assert_not_called()
        get_regional_energy_mix_data.assert_not_called()

    def test_try_get_nordic_region_emissions_returns_none_if_region_data_missing(self):
        # GIVEN
        energy = Energy.from_energy(kWh=1.0)
        geo = GeoMetadata(country_iso_code="SWE", country_name="Sweden", region="SE2")

        # WHEN
        with patch.object(
            self._data_source,
            "get_nordic_country_energy_mix_data",
            return_value={"data": {}},
        ):
            emissions = self._emissions._try_get_nordic_region_emissions(energy, geo)

        # THEN
        self.assertIsNone(emissions)

    def test_try_get_nordic_region_emissions_returns_none_on_data_loading_error(self):
        # GIVEN
        energy = Energy.from_energy(kWh=1.0)
        geo = GeoMetadata(country_iso_code="SWE", country_name="Sweden", region="SE2")

        # WHEN
        with patch.object(
            self._data_source,
            "get_nordic_country_energy_mix_data",
            side_effect=Exception("boom"),
        ):
            emissions = self._emissions._try_get_nordic_region_emissions(energy, geo)

        # THEN
        self.assertIsNone(emissions)

    def _china_geo(self, region, country_iso_code="CHN", country_name="China"):
        return GeoMetadata(
            country_iso_code=country_iso_code, country_name=country_name, region=region
        )

    def test_get_emissions_PRIVATE_INFRA_CHINA_PROVINCE(self):
        # WHEN
        emissions = self._emissions.get_private_infra_emissions(
            Energy.from_energy(kWh=2.0), self._china_geo("Sichuan")
        )

        # THEN
        # Sichuan: 0.1564 kgCO2/kWh in the 2023 MEE/NBS table
        assert isinstance(emissions, float)
        self.assertAlmostEqual(emissions, 2.0 * 0.1564, places=6)

    def test_china_province_factors_match_official_table(self):
        data = self._data_source.get_china_provincial_emissions_data()["data"]

        self.assertEqual(len(data), 30)
        self.assertNotIn("CN-XZ", data)
        self.assertAlmostEqual(data["CN-GD"]["emission_factor"], 441.9)
        self.assertAlmostEqual(data["CN-YN"]["emission_factor"], 133.3)
        self.assertAlmostEqual(data["CN-TJ"]["emission_factor"], 679.6)

    def test_china_province_name_variants(self):
        expected_by_region = {
            "beijing": "CN-BJ",
            "Shanghai": "CN-SH",
            "TIANJIN": "CN-TJ",
            "Chongqing": "CN-CQ",
            "Inner Mongolia": "CN-NM",
            "inner mongolia autonomous region": "CN-NM",
            "Nei Mongol": "CN-NM",
            "Ningxia": "CN-NX",
            "Ningxia Hui": "CN-NX",
            "Ningxia Hui Autonomous Region": "CN-NX",
            "Xinjiang": "CN-XJ",
            "Xinjiang Uygur": "CN-XJ",
            "Xinjiang Uyghur Autonomous Region": "CN-XJ",
            "Guangxi": "CN-GX",
            "Guangxi Zhuang": "CN-GX",
            "  Guangdong  Province ": "CN-GD",
            "Shaanxi": "CN-SN",
            "Shanxi": "CN-SX",
        }
        data = self._data_source.get_china_provincial_emissions_data()["data"]
        energy = Energy.from_energy(kWh=1.0)

        for region, key in expected_by_region.items():
            with self.subTest(region=region):
                emissions = self._emissions.get_private_infra_emissions(
                    energy, self._china_geo(region)
                )
                self.assertAlmostEqual(
                    emissions, data[key]["emission_factor"] / 1000, places=6
                )

    def test_china_every_province_resolves_to_its_own_factor(self):
        data = self._data_source.get_china_provincial_emissions_data()["data"]
        energy = Energy.from_energy(kWh=1.0)

        for key, province in data.items():
            with self.subTest(province=key):
                emissions = self._emissions.get_private_infra_emissions(
                    energy, self._china_geo(province["description"])
                )
                self.assertAlmostEqual(
                    emissions, province["emission_factor"] / 1000, places=6
                )

    def test_china_province_names_are_unique(self):
        data = self._data_source.get_china_provincial_emissions_data()["data"]
        names = [name for province in data.values() for name in province["names"]]

        self.assertEqual(len(names), len(set(names)))

    def test_china_unpublished_or_unknown_regions_fall_back_to_national_value(self):
        energy = Energy.from_energy(kWh=1.0)
        national = self._emissions.get_country_emissions(energy, self._china_geo(None))

        for region in [None, "Tibet", "Xizang", "Hong Kong", "Macao", "Taiwan", "xyz"]:
            with self.subTest(region=region):
                emissions = self._emissions.get_private_infra_emissions(
                    energy, self._china_geo(region)
                )
                self.assertAlmostEqual(emissions, national, places=6)

    def test_china_fallback_does_not_log_warnings_or_errors(self):
        with (
            patch("codecarbon.core.emissions.logger.error") as log_error,
            patch("codecarbon.core.emissions.logger.warning") as log_warning,
        ):
            self._emissions.get_private_infra_emissions(
                Energy.from_energy(kWh=1.0), self._china_geo("Tibet")
            )

        log_error.assert_not_called()
        log_warning.assert_not_called()

    def test_china_province_name_outside_china_is_not_used(self):
        energy = Energy.from_energy(kWh=1.0)
        for country_iso_code, country_name in [
            ("HKG", "Hong Kong"),
            ("TWN", "Taiwan"),
            ("MAC", "Macao"),
            ("FRA", "France"),
        ]:
            with self.subTest(country_iso_code=country_iso_code):
                geo = self._china_geo("Guangdong", country_iso_code, country_name)
                emissions = self._emissions.get_private_infra_emissions(energy, geo)
                self.assertAlmostEqual(
                    emissions,
                    self._emissions.get_country_emissions(energy, geo),
                    places=6,
                )

    def test_china_province_data_error_falls_back_to_national_value(self):
        energy = Energy.from_energy(kWh=1.0)
        national = self._emissions.get_country_emissions(energy, self._china_geo(None))

        with patch.object(
            self._data_source,
            "get_china_provincial_emissions_data",
            side_effect=OSError("missing"),
        ):
            emissions = self._emissions.get_private_infra_emissions(
                energy, self._china_geo("Sichuan")
            )

        self.assertAlmostEqual(emissions, national, places=6)

    def test_china_forced_intensity_takes_precedence(self):
        emissions_calculator = Emissions(
            self._data_source, force_carbon_intensity_g_co2e_kwh=100.0
        )

        emissions = emissions_calculator.get_private_infra_emissions(
            Energy.from_energy(kWh=1.0), self._china_geo("Sichuan")
        )

        self.assertAlmostEqual(emissions, 0.1, places=6)

    def _usa_geo(self, region):
        return GeoMetadata(
            country_iso_code="USA", country_name="United States", region=region
        )

    def test_usa_state_rates_match_egrid2023(self):
        data = self._data_source.get_country_emissions_data("usa")

        self.assertEqual(data["_source"]["year"], 2023)
        self.assertEqual(data["_source"]["field"], "STC2ERTA")
        states = {k: v for k, v in data.items() if not k.startswith("_")}
        self.assertEqual(len(states), 52)
        self.assertAlmostEqual(data["georgia"]["emissions"], 717.4, delta=0.05)
        self.assertAlmostEqual(data["vermont"]["emissions"], 52.2, delta=0.05)
        self.assertAlmostEqual(data["west virginia"]["emissions"], 1968.9, delta=0.05)
        self.assertAlmostEqual(data["usa"]["emissions"], 770.9, delta=0.05)

    def test_usa_every_state_resolves_to_its_own_rate(self):
        data = self._data_source.get_country_emissions_data("usa")
        energy = Energy.from_energy(kWh=1.0)

        for name, state in data.items():
            if name.startswith("_") or name == "usa":
                continue
            with self.subTest(state=name):
                emissions = self._emissions.get_private_infra_emissions(
                    energy, self._usa_geo(name.title())
                )
                self.assertAlmostEqual(
                    emissions, state["emissions"] * 0.00045359237, places=9
                )
