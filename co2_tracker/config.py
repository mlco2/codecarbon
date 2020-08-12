"""
App configuration: This will likely change when we have a common location for data files
"""

from dataclasses import dataclass
import pkg_resources

cfg = {
    "geo_js_url": "https://get.geojs.io/v1/ip/geo.json",
    "cloud_emissions_path": "data/cloud/impact.csv",
    "private_infra_us_path": "data/private_infra/2016/us_emissions.json",
    "private_infra_global_energy_mix_path": "data/private_infra/2016/global_energy_mix.json",
}


@dataclass
class AppConfig:
    def __init__(self):
        self.config = cfg
        self.module_name = "co2_tracker"

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

    @property
    def private_infra_us_path(self):
        return pkg_resources.resource_filename(
            self.module_name, self.config["private_infra_us_path"]
        )

    @property
    def private_infra_energy_mix_path(self):
        return pkg_resources.resource_filename(
            self.module_name, self.config["private_infra_energy_mix_path"]
        )
