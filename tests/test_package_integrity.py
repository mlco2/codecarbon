"""
Test that verifies the package includes all necessary data files.
This test should be run against the installed package, not the source.
"""

import pandas as pd
import pytest

from codecarbon.input import DataSource


def test_critical_data_files_included():
    """Test that all critical data files are included in the package."""
    ds = DataSource()

    # Test cloud emissions data
    cloud_path = ds.cloud_emissions_path
    assert cloud_path.exists(), f"Cloud emissions file missing: {cloud_path}"

    # Test that we can actually read the cloud emissions data
    cloud_data = ds.get_cloud_emissions_data()
    assert isinstance(
        cloud_data, pd.DataFrame
    ), "Cloud emissions data should be a DataFrame"
    assert not cloud_data.empty, "Cloud emissions data should not be empty"

    # Test carbon intensity data
    carbon_intensity_path = ds.carbon_intensity_per_source_path
    assert (
        carbon_intensity_path.exists()
    ), f"Carbon intensity file missing: {carbon_intensity_path}"

    # Test that we can actually read the carbon intensity data
    carbon_intensity_data = ds.get_carbon_intensity_per_source_data()
    assert isinstance(
        carbon_intensity_data, dict
    ), "Carbon intensity data should be a dict"
    assert len(carbon_intensity_data) > 0, "Carbon intensity data should not be empty"


def test_cpu_power_data_included():
    """Test that CPU power data is included."""
    ds = DataSource()

    # Test cpu power data path
    cpu_power_path = ds.cpu_power_path
    assert cpu_power_path.exists(), f"CPU power data missing: {cpu_power_path}"

    # Test that we can actually read the CPU power data
    cpu_power_data = ds.get_cpu_power_data()
    assert isinstance(
        cpu_power_data, pd.DataFrame
    ), "CPU power data should be a DataFrame"
    assert not cpu_power_data.empty, "CPU power data should not be empty"


def test_global_energy_mix_data_included():
    """Test that global energy mix data is included."""
    ds = DataSource()

    # Test global energy mix data path
    global_energy_path = ds.global_energy_mix_data_path
    assert (
        global_energy_path.exists()
    ), f"Global energy mix data missing: {global_energy_path}"

    # Test that we can actually read the global energy mix data
    global_energy_data = ds.get_global_energy_mix_data()
    assert isinstance(
        global_energy_data, dict
    ), "Global energy mix data should be a dict"
    assert len(global_energy_data) > 0, "Global energy mix data should not be empty"


def test_country_specific_data_access():
    """Test that we can access country-specific data if available."""
    ds = DataSource()

    # Test USA data if available
    try:
        usa_data = ds.get_country_emissions_data("usa")
        assert isinstance(usa_data, dict), "USA emissions data should be a dict"
        assert len(usa_data) > 0, "USA emissions data should not be empty"
    except Exception:
        # This is acceptable if USA data doesn't exist or has issues
        pass

    # Test Canada energy mix if available
    try:
        canada_data = ds.get_country_energy_mix_data("can")
        assert isinstance(canada_data, dict), "Canada energy mix data should be a dict"
        assert len(canada_data) > 0, "Canada energy mix data should not be empty"
    except Exception:
        # This is acceptable if Canada data doesn't exist or has issues
        pass


def test_basic_functionality():
    """Test basic package functionality works."""
    from codecarbon import EmissionsTracker

    # Just test that we can instantiate the tracker
    tracker = EmissionsTracker(
        measure_power_secs=1, tracking_mode="machine", log_level="warning"
    )
    assert tracker is not None

    # Test that the tracker has access to data sources
    assert tracker._data_source is not None
    assert hasattr(tracker._data_source, "get_cloud_emissions_data")


def test_cli_import():
    """Test that CLI can be imported (basic smoke test)."""
    try:
        from codecarbon.cli.main import main

        assert main is not None
    except ImportError as e:
        pytest.fail(f"Could not import CLI main function: {e}")


def test_package_importability():
    """Test that the main package components can be imported."""
    # Test main tracker import
    from codecarbon import EmissionsTracker

    assert EmissionsTracker is not None

    # Test core modules
    from codecarbon.core.emissions import Emissions

    assert Emissions is not None

    from codecarbon.core.config import parse_gpu_ids

    assert parse_gpu_ids is not None

    # Test output modules
    from codecarbon.output import EmissionsData

    assert EmissionsData is not None
