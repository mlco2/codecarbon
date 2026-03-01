"""
App configuration and static reference data loading.

Data files are static reference data that never change during runtime.
They are loaded once at module import to avoid repeated file I/O on the hot path
(start_task/stop_task calls for instance).
"""

import atexit
import json
from contextlib import ExitStack
from importlib.resources import as_file as importlib_resources_as_file
from importlib.resources import files as importlib_resources_files
from typing import Any, Dict

import pandas as pd

_CACHE: Dict[str, Any] = {}
_MODULE_NAME = "codecarbon"


def _get_resource_path(filepath: str):
    """Get filesystem path to a package resource file."""
    file_manager = ExitStack()
    atexit.register(file_manager.close)
    ref = importlib_resources_files(_MODULE_NAME).joinpath(filepath)
    path = file_manager.enter_context(importlib_resources_as_file(ref))
    return path


def _load_static_data() -> None:
    """
    Load all static reference data at module import.

    Called once when codecarbon is imported. All data loaded here
    is immutable and shared across all tracker instances.
    """
    # Global energy mix - used for emissions calculations
    path = _get_resource_path("data/private_infra/global_energy_mix.json")
    with open(path) as f:
        _CACHE["global_energy_mix"] = json.load(f)

    # Cloud emissions data
    path = _get_resource_path("data/cloud/impact.csv")
    _CACHE["cloud_emissions"] = pd.read_csv(path)

    # Carbon intensity per source
    path = _get_resource_path("data/private_infra/carbon_intensity_per_source.json")
    with open(path) as f:
        _CACHE["carbon_intensity_per_source"] = json.load(f)

    # CPU power data
    path = _get_resource_path("data/hardware/cpu_power.csv")
    _CACHE["cpu_power"] = pd.read_csv(path)


# Load static data at module import
_load_static_data()


class DataSource:
    def __init__(self):
        self.config = {
            "geo_js_url": "https://get.geojs.io/v1/ip/geo.json",
            "cloud_emissions_path": "data/cloud/impact.csv",
            "usa_emissions_data_path": "data/private_infra/2016/usa_emissions.json",
            "can_energy_mix_data_path": "data/private_infra/2023/canada_energy_mix.json",  # noqa: E501
            "global_energy_mix_data_path": "data/private_infra/global_energy_mix.json",  # noqa: E501
            "carbon_intensity_per_source_path": "data/private_infra/carbon_intensity_per_source.json",
            "cpu_power_path": "data/hardware/cpu_power.csv",
        }
        self.module_name = "codecarbon"

    @property
    def geo_js_url(self):
        return self.config["geo_js_url"]

    @staticmethod
    def get_ressource_path(package: str, filepath: str):
        file_manager = ExitStack()
        atexit.register(file_manager.close)
        ref = importlib_resources_files(package).joinpath(filepath)
        path = file_manager.enter_context(importlib_resources_as_file(ref))
        return path

    @property
    def cloud_emissions_path(self):
        """
        Resource Extraction from a package
        https://setuptools.readthedocs.io/en/latest/pkg_resources.html#resource-extraction
        """
        return self.get_ressource_path(
            self.module_name, self.config["cloud_emissions_path"]
        )

    @property
    def carbon_intensity_per_source_path(self):
        """
        Get the path from the package resources.
        """
        return self.get_ressource_path(
            self.module_name, self.config["carbon_intensity_per_source_path"]
        )

    def country_emissions_data_path(self, country: str):
        return self.get_ressource_path(
            self.module_name, self.config[f"{country}_emissions_data_path"]
        )

    def country_energy_mix_data_path(self, country: str):
        return self.get_ressource_path(
            self.module_name, self.config[f"{country}_energy_mix_data_path"]
        )

    @property
    def global_energy_mix_data_path(self):
        return self.get_ressource_path(
            self.module_name, self.config["global_energy_mix_data_path"]
        )

    @property
    def cpu_power_path(self):
        return self.get_ressource_path(self.module_name, self.config["cpu_power_path"])

    def get_global_energy_mix_data(self) -> Dict:
        """
        Returns Global Energy Mix Data.
        Data is pre-loaded at module import for performance.
        """
        return _CACHE["global_energy_mix"]

    def get_cloud_emissions_data(self) -> pd.DataFrame:
        """
        Returns Cloud Regions Impact Data.
        Data is pre-loaded at module import for performance.
        """
        return _CACHE["cloud_emissions"]

    def get_country_emissions_data(self, country_iso_code: str) -> Dict:
        """
        Returns Emissions Across Regions in a country.
        Data is cached on first access per country.

        :param country_iso_code: ISO code similar to one used in file names
        :return: emissions in lbs/MWh and region code
        """
        cache_key = f"country_emissions_{country_iso_code}"
        if cache_key not in _CACHE:
            try:
                with open(self.country_emissions_data_path(country_iso_code)) as f:
                    _CACHE[cache_key] = json.load(f)
            except KeyError:
                # KeyError raised when there is no data path specified for the country
                raise DataSourceException
        return _CACHE[cache_key]

    def get_country_energy_mix_data(self, country_iso_code: str) -> Dict:
        """
        Returns Energy Mix Across Regions in a country.
        Data is cached on first access per country.

        :param country_iso_code: ISO code similar to one used in file names
        :return: energy mix by region code
        """
        cache_key = f"country_energy_mix_{country_iso_code}"
        if cache_key not in _CACHE:
            with open(self.country_energy_mix_data_path(country_iso_code)) as f:
                _CACHE[cache_key] = json.load(f)
        return _CACHE[cache_key]

    def get_carbon_intensity_per_source_data(self) -> Dict:
        """
        Returns Carbon intensity per source. In gCO2.eq/kWh.
        Data is pre-loaded at module import for performance.
        """
        return _CACHE["carbon_intensity_per_source"]

    def get_cpu_power_data(self) -> pd.DataFrame:
        """
        Returns CPU power Data.
        Data is pre-loaded at module import for performance.
        """
        return _CACHE["cpu_power"]


class DataSourceException(Exception):
    pass
