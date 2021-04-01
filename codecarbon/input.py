"""
App configuration: This will likely change when we have a common location for data files
"""

import json
from typing import Dict

import pandas as pd
import pkg_resources


class DataSource:
    def __init__(self):
        self.config = {
            "geo_js_url": "https://get.geojs.io/v1/ip/geo.json",
            "cloud_emissions_path": "data/cloud/impact.csv",
            "usa_emissions_data_path": "data/private_infra/2016/usa_emissions.json",
            "can_energy_mix_data_path": "data/private_infra/2016/canada_energy_mix.json",
            "global_energy_mix_data_path": "data/private_infra/2016/global_energy_mix.json",
            "cpu_power_path": "data/hardware/cpu_power.csv",
        }
        self.module_name = "codecarbon"

    @property
    def geo_js_url(self):
        return self.config["geo_js_url"]

    @property
    def cloud_emissions_path(self):
        """
        Resource Extraction from a package
        https://setuptools.readthedocs.io/en/latest/pkg_resources.html#resource-extraction
        """
        return pkg_resources.resource_filename(
            self.module_name, self.config["cloud_emissions_path"]
        )

    def country_emissions_data_path(self, country: str):
        return pkg_resources.resource_filename(
            self.module_name, self.config[f"{country}_emissions_data_path"]
        )

    def country_energy_mix_data_path(self, country: str):
        return pkg_resources.resource_filename(
            self.module_name, self.config[f"{country}_energy_mix_data_path"]
        )

    @property
    def global_energy_mix_data_path(self):
        return pkg_resources.resource_filename(
            self.module_name, self.config["global_energy_mix_data_path"]
        )

    @property
    def cpu_power_path(self):
        return pkg_resources.resource_filename(
            self.module_name, self.config["cpu_power_path"]
        )

    def get_global_energy_mix_data(self) -> Dict:
        """
        Returns Global Energy Mix Data
        """
        with open(self.global_energy_mix_data_path) as f:
            global_energy_mix: Dict = json.load(f)
        return global_energy_mix

    def get_cloud_emissions_data(self) -> pd.DataFrame:
        """
        Returns Cloud Regions Impact Data
        """
        return pd.read_csv(self.cloud_emissions_path)

    def get_country_emissions_data(self, country_iso_code: str) -> Dict:
        """
        Returns Emissions Across Regions in a country
        :param country_iso_code: ISO code similar to one used in file names
        :return: emissions in lbs/MWh and region code
        """
        try:
            with open(self.country_emissions_data_path(country_iso_code)) as f:
                country_emissions_data: Dict = json.load(f)
            return country_emissions_data
        except KeyError:  # KeyError raised from line 39, when there is no data path specified for the given country
            raise DataSourceException

    def get_country_energy_mix_data(self, country_iso_code: str) -> Dict:
        """
        Returns Energy Mix Across Regions in a country
        :param country_iso_code: ISO code similar to one used in file names
        :return: energy mix by region code
        """
        with open(self.country_energy_mix_data_path(country_iso_code)) as f:
            country_energy_mix_data: Dict = json.load(f)
        return country_energy_mix_data

    def get_cpu_power_data(self) -> pd.DataFrame:
        """
        Returns CPU power Data
        """
        return pd.read_csv(self.cpu_power_path)


class DataSourceException(Exception):
    pass
