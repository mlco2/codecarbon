import types
import unittest
import unittest.mock

from codecarbon.core.units import Energy, Water, WaterPerKWh
from codecarbon.core.water_consumption import WaterConsumption
from codecarbon.emissions_tracker import BaseEmissionsTracker
from codecarbon.external.geography import CloudMetadata, GeoMetadata
from codecarbon.input import DataSource
from tests.testutils import get_test_data_source

# World average water intensity of electricity, in L/kWh
# 991.66 gal us/MWh * 3.785411784 L/gal / 1000
WORLD_AVERAGE_L_PER_KWH = 3.75


class TestWaterPerKWh(unittest.TestCase):
    def test_from_gal_us_per_MWh(self):
        water = WaterPerKWh.from_gal_us_per_MWh(1000)
        self.assertAlmostEqual(water.l_per_kWh, 3.785411784, places=6)

    def test_l_per_kWh(self):
        self.assertEqual(WaterPerKWh(l_per_kWh=1.5).l_per_kWh, 1.5)


class TestWaterConsumption(unittest.TestCase):
    def setUp(self) -> None:
        # GIVEN
        self._data_source = get_test_data_source()
        self._water = WaterConsumption(self._data_source)

    def test_water_consumption_per_source_data(self):
        water_per_source = DataSource().get_water_consumption_per_source_data()
        # The keys must match the source names of global_energy_mix.json
        # (without the _TWh suffix) for the energy mix computation to work.
        for source in [
            "coal",
            "gas",
            "oil",
            "nuclear",
            "hydroelectricity",
            "biofuel",
            "solar",
            "wind",
            "world_average",
        ]:
            self.assertIn(source, water_per_source)
            self.assertGreater(water_per_source[source], 0)

    def test_water_consumption_covers_energy_mix(self):
        """
        The water consumption sources must cover most of the energy mix of
        most countries, else everything falls back to the world average.
        """
        water_per_source = DataSource().get_water_consumption_per_source_data()
        energy_mix = self._data_source.get_global_energy_mix_data()
        low_coverage_countries = []
        for iso, mix in energy_mix.items():
            if not isinstance(mix, dict) or not mix.get("total_TWh"):
                continue
            covered = sum(
                energy or 0
                for source, energy in mix.items()
                if source.endswith("_TWh")
                and source[: -len("_TWh")] in water_per_source
            )
            if covered / mix["total_TWh"] < WaterConsumption.MIN_ENERGY_MIX_COVERAGE:
                low_coverage_countries.append(iso)
        # A few geothermal-heavy countries (e.g. Kenya, Iceland) are expected
        # to fall back to the world average.
        self.assertLess(len(low_coverage_countries), 10)

    def test_get_water_consumption_PRIVATE_INFRA_FRA(self):
        # WHEN
        water = self._water.get_private_infra_water_consumption(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="FRA", country_name="France"),
        )
        # THEN: nuclear and hydro heavy mix, well above the world average
        self.assertIsInstance(water, float)
        self.assertGreater(water, 2)
        self.assertLess(water, 6)

    def test_get_water_consumption_PRIVATE_INFRA_POL(self):
        # WHEN: Poland has a coal-heavy mix
        water = self._water.get_private_infra_water_consumption(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="POL", country_name="Poland"),
        )
        # THEN: close to the coal intensity (550 gal us/MWh ~ 2.08 L/kWh)
        self.assertGreater(water, 1)
        self.assertLess(water, 3)

    def test_water_consumption_scales_with_energy(self):
        geo = GeoMetadata(country_iso_code="FRA", country_name="France")
        water_1 = self._water.get_private_infra_water_consumption(
            Energy.from_energy(kWh=1), geo
        )
        water_10 = self._water.get_private_infra_water_consumption(
            Energy.from_energy(kWh=10), geo
        )
        self.assertAlmostEqual(water_10, 10 * water_1, places=6)

    def test_get_water_consumption_PRIVATE_INFRA_unknown_country(self):
        # WHEN
        water = self._water.get_private_infra_water_consumption(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="XXX", country_name="Atlantis"),
        )
        # THEN: world average
        self.assertAlmostEqual(water, WORLD_AVERAGE_L_PER_KWH, places=2)

    def test_get_water_consumption_PRIVATE_INFRA_low_coverage_country(self):
        # WHEN: more than 10% of Kenya's electricity comes from geothermal,
        # which is not a source of global_energy_mix.json
        water = self._water.get_private_infra_water_consumption(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="KEN", country_name="Kenya"),
        )
        # THEN: world average fallback
        self.assertAlmostEqual(water, WORLD_AVERAGE_L_PER_KWH, places=2)

    def test_get_water_consumption_PRIVATE_INFRA_CANADA_region(self):
        # WHEN: hydro-heavy Canadian region
        water = self._water.get_region_water_consumption(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="CAN", country_name="Canada", region="quebec"),
        )
        # THEN: dominated by the hydro intensity (4491 gal us/MWh ~ 17 L/kWh)
        self.assertGreater(water, 10)
        self.assertLess(water, 20)

    def test_get_water_consumption_PRIVATE_INFRA_USA_region_falls_back(self):
        # WHEN: there is no regional energy mix data for the USA (only
        # regional emissions data), so the country value must be used
        water_region = self._water.get_private_infra_water_consumption(
            Energy.from_energy(kWh=1),
            GeoMetadata(
                country_iso_code="USA",
                country_name="United States",
                region="california",
            ),
        )
        water_country = self._water.get_country_water_consumption(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="USA", country_name="United States"),
        )
        self.assertAlmostEqual(water_region, water_country, places=6)

    def test_water_intensity_is_cached_per_location(self):
        # WHEN: computing twice for the same location
        geo = GeoMetadata(country_iso_code="FRA", country_name="France")
        self._water.get_private_infra_water_consumption(Energy.from_energy(kWh=1), geo)
        # THEN: the energy mix is not read again, the tracker calls this on
        # every measurement cycle
        with unittest.mock.patch.object(
            self._data_source, "get_global_energy_mix_data"
        ) as mocked_energy_mix:
            self._water.get_private_infra_water_consumption(
                Energy.from_energy(kWh=1), geo
            )
            mocked_energy_mix.assert_not_called()

    def test_get_water_consumption_CLOUD_with_geo_fallback(self):
        # WHEN: no cloud water data exists, so the country of the machine
        # is used
        water = self._water.get_cloud_water_consumption(
            Energy.from_energy(kWh=1),
            CloudMetadata(provider="aws", region="eu-west-1"),
            GeoMetadata(country_iso_code="FRA", country_name="France"),
        )
        water_country = self._water.get_private_infra_water_consumption(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="FRA", country_name="France"),
        )
        self.assertAlmostEqual(water, water_country, places=6)

    def test_get_water_consumption_CLOUD_without_geo(self):
        # WHEN
        water = self._water.get_cloud_water_consumption(
            Energy.from_energy(kWh=1),
            CloudMetadata(provider="aws", region="eu-west-1"),
        )
        # THEN: world average
        self.assertAlmostEqual(water, WORLD_AVERAGE_L_PER_KWH, places=2)


class TestWaterConsumptionSyntheticMix(unittest.TestCase):
    """Hand-computed cases on a 50% coal / 50% wind mix.

    (0.5 * 550 + 0.5 * 11) = 280.5 gal us/MWh
    280.5 * 3.785411784 / 1000 = 1.061808 L/kWh
    """

    L_PER_KWH = 1.061808

    def _source(self, global_mix, region_mix=None):
        source = unittest.mock.MagicMock()
        source.get_global_energy_mix_data.return_value = global_mix
        source.get_water_consumption_per_source_data.return_value = {
            "coal": 550,
            "wind": 11,
            "world_average": 1000,
        }
        if region_mix is None:
            source.get_country_energy_mix_data.side_effect = KeyError("no file")
        else:
            source.get_country_energy_mix_data.return_value = region_mix
        return source

    def test_country_water_consumption(self):
        mix = {"XXX": {"coal_TWh": 50, "wind_TWh": 50, "total_TWh": 100}}
        water = WaterConsumption(self._source(mix)).get_country_water_consumption(
            Energy.from_energy(kWh=2),
            GeoMetadata(country_iso_code="XXX", country_name="Xland"),
        )
        self.assertAlmostEqual(water, 2 * self.L_PER_KWH, places=5)

    def test_region_water_consumption(self):
        region_mix = {"qc": {"coal": 50, "wind": 50, "total": 100}}
        water = WaterConsumption(
            self._source({}, region_mix)
        ).get_region_water_consumption(
            Energy.from_energy(kWh=2),
            GeoMetadata(country_iso_code="CAN", country_name="Canada", region="QC"),
        )
        self.assertAlmostEqual(water, 2 * self.L_PER_KWH, places=5)

    def test_canada_region_failure_falls_back_to_country(self):
        mix = {"CAN": {"coal_TWh": 50, "wind_TWh": 50, "total_TWh": 100}}
        water = WaterConsumption(self._source(mix)).get_private_infra_water_consumption(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="CAN", country_name="Canada", region="QC"),
        )
        self.assertAlmostEqual(water, self.L_PER_KWH, places=5)

    def test_zero_total_energy_uses_world_average(self):
        mix = {"XXX": {"coal_TWh": 0, "total_TWh": 0}}
        water = WaterConsumption(self._source(mix)).get_country_water_consumption(
            Energy.from_energy(kWh=1),
            GeoMetadata(country_iso_code="XXX", country_name="Xland"),
        )
        # world_average 1000 gal us/MWh = 3.785411784 L/kWh
        self.assertAlmostEqual(water, 3.785412, places=5)


class TestTrackerUpdateWater(unittest.TestCase):
    def _tracker(self):
        return types.SimpleNamespace(
            _water_consumption=unittest.mock.MagicMock(),
            _geo="geo",
            _total_water=Water.from_litres(litres=1.0),
        )

    def test_private_infra_adds_to_total(self):
        t = self._tracker()
        t._water_consumption.get_private_infra_water_consumption.return_value = 0.5
        BaseEmissionsTracker._update_water(
            t, Energy.from_energy(kWh=1), CloudMetadata(provider=None, region=None)
        )
        self.assertEqual(t._total_water.litres, 1.5)

    def test_cloud_adds_to_total(self):
        t = self._tracker()
        t._water_consumption.get_cloud_water_consumption.return_value = 2.0
        BaseEmissionsTracker._update_water(
            t, Energy.from_energy(kWh=1), CloudMetadata(provider="aws", region="x")
        )
        self.assertEqual(t._total_water.litres, 3.0)

    def test_failure_is_swallowed(self):
        t = self._tracker()
        t._water_consumption.get_private_infra_water_consumption.side_effect = (
            RuntimeError("boom")
        )
        BaseEmissionsTracker._update_water(
            t, Energy.from_energy(kWh=1), CloudMetadata(provider=None, region=None)
        )
        self.assertEqual(t._total_water.litres, 1.0)


if __name__ == "__main__":
    unittest.main()
