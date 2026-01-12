"""
Tests for codecarbon/input.py module-level caching.

The caching mechanism loads static reference data once at module import
to avoid file I/O on the hot path (start_task/stop_task).
"""

import unittest


class TestDataSourceCaching(unittest.TestCase):
    """Test that DataSource uses module-level cache for static data."""

    def test_cache_populated_at_import(self):
        """Verify that _CACHE is populated when module is imported."""
        from codecarbon.input import _CACHE

        # All static data should be pre-loaded
        self.assertIn("global_energy_mix", _CACHE)
        self.assertIn("cloud_emissions", _CACHE)
        self.assertIn("carbon_intensity_per_source", _CACHE)
        self.assertIn("cpu_power", _CACHE)

        # Verify data is non-empty
        self.assertGreater(len(_CACHE["global_energy_mix"]), 0)
        self.assertGreater(len(_CACHE["cloud_emissions"]), 0)
        self.assertGreater(len(_CACHE["carbon_intensity_per_source"]), 0)
        self.assertGreater(len(_CACHE["cpu_power"]), 0)

    def test_get_global_energy_mix_returns_cached_data(self):
        """Verify get_global_energy_mix_data() returns cached object."""
        from codecarbon.input import _CACHE, DataSource

        ds = DataSource()
        data = ds.get_global_energy_mix_data()

        # Should return the exact same object from cache
        self.assertIs(data, _CACHE["global_energy_mix"])

    def test_get_cloud_emissions_returns_cached_data(self):
        """Verify get_cloud_emissions_data() returns cached object."""
        from codecarbon.input import _CACHE, DataSource

        ds = DataSource()
        data = ds.get_cloud_emissions_data()

        # Should return the exact same object from cache
        self.assertIs(data, _CACHE["cloud_emissions"])

    def test_get_carbon_intensity_returns_cached_data(self):
        """Verify get_carbon_intensity_per_source_data() returns cached object."""
        from codecarbon.input import _CACHE, DataSource

        ds = DataSource()
        data = ds.get_carbon_intensity_per_source_data()

        # Should return the exact same object from cache
        self.assertIs(data, _CACHE["carbon_intensity_per_source"])

    def test_get_cpu_power_returns_cached_data(self):
        """Verify get_cpu_power_data() returns cached object."""
        from codecarbon.input import _CACHE, DataSource

        ds = DataSource()
        data = ds.get_cpu_power_data()

        # Should return the exact same object from cache
        self.assertIs(data, _CACHE["cpu_power"])

    def test_country_data_lazy_loaded(self):
        """Verify country-specific data is lazy-loaded and cached."""
        from codecarbon.input import _CACHE, DataSource

        ds = DataSource()
        cache_key = "country_emissions_usa"

        # USA data may or may not be cached depending on prior test runs
        # Just verify that after calling, it IS cached
        data = ds.get_country_emissions_data("usa")
        self.assertIn(cache_key, _CACHE)
        self.assertIs(data, _CACHE[cache_key])

    def test_multiple_datasource_instances_share_cache(self):
        """Verify that multiple DataSource instances share the same cache."""
        from codecarbon.input import DataSource

        ds1 = DataSource()
        ds2 = DataSource()

        # Both instances should return the same cached object
        data1 = ds1.get_global_energy_mix_data()
        data2 = ds2.get_global_energy_mix_data()

        self.assertIs(data1, data2)


if __name__ == "__main__":
    unittest.main()
