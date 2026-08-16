"""
App configuration and static reference data loading.

Static CSV/JSON reference data is loaded lazily on first DataSource access
to keep `import codecarbon` fast for measurement startup.
"""

from __future__ import annotations

import atexit
import csv
import json
import warnings
from contextlib import ExitStack
from importlib.resources import as_file as importlib_resources_as_file
from importlib.resources import files as importlib_resources_files
from typing import Any, Dict

_CACHE: Dict[str, Any] = {}
_MODULE_NAME = "codecarbon"


def _get_resource_path(filepath: str):
    """Get filesystem path to a package resource file."""
    file_manager = ExitStack()
    atexit.register(file_manager.close)
    ref = importlib_resources_files(_MODULE_NAME).joinpath(filepath)
    path = file_manager.enter_context(importlib_resources_as_file(ref))
    return path


def _read_csv(path, numeric_columns=()) -> list[dict[str, Any]]:
    """
    Read a bundled reference CSV into a list of row dicts.

    ``utf-8-sig`` is required: ``data/cloud/impact.csv`` starts with a UTF-8 BOM,
    which would otherwise end up glued to the first column name. Empty fields
    become ``None`` (not ``""``) so callers can test them with ``is None``, and
    the columns listed in ``numeric_columns`` are coerced to ``float`` at this
    boundary rather than being left as strings for callers to guess about.
    """
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = []
        for raw in csv.DictReader(f):
            row: dict[str, Any] = {k: (v if v else None) for k, v in raw.items()}
            for column in numeric_columns:
                if row.get(column) is not None:
                    row[column] = float(row[column])
            rows.append(row)
        return rows


def _deprecated_rows_accessor(old: str, new: str) -> None:
    warnings.warn(
        f"DataSource.{old}() no longer returns a pandas DataFrame; it returns a "
        f"list of row dicts. Use DataSource.{new}() instead. "
        f"{old}() will be removed in a future version.",
        DeprecationWarning,
        stacklevel=3,
    )


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
    _CACHE["cloud_emissions"] = _read_csv(
        path, numeric_columns=("impact", "offsetRatio")
    )

    # Carbon intensity per source
    path = _get_resource_path("data/private_infra/carbon_intensity_per_source.json")
    with open(path) as f:
        _CACHE["carbon_intensity_per_source"] = json.load(f)

    # CPU power data
    path = _get_resource_path("data/hardware/cpu_power.csv")
    # TDP is deliberately left as text: a handful of rows hold malformed values
    # such as "27.29.5", and coercing here would fail the whole load instead of
    # only the lookup for those CPUs (which is what happens today).
    _CACHE["cpu_power"] = _read_csv(path)

    # Nordic country energy mix - used for emissions calculations
    path = _get_resource_path("data/private_infra/nordic_emissions.json")
    with open(path) as f:
        _CACHE["nordic_country_energy_mix"] = json.load(f)


_STATIC_DATA_LOADED = False


def _ensure_static_data_loaded() -> None:
    """Load immutable reference data on first use instead of at import."""
    global _STATIC_DATA_LOADED
    if _STATIC_DATA_LOADED:
        return
    _load_static_data()
    _STATIC_DATA_LOADED = True


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
        Data is loaded on first access and cached for all tracker instances.
        """
        _ensure_static_data_loaded()
        return _CACHE["global_energy_mix"]

    def get_cloud_emissions_rows(self) -> list[dict[str, Any]]:
        """
        Returns Cloud Regions Impact Data, as one dict per row.
        Data is loaded on first access and cached for all tracker instances.
        """
        _ensure_static_data_loaded()
        return _CACHE["cloud_emissions"]

    def get_cloud_emissions_data(self) -> list[dict[str, Any]]:
        """
        Deprecated alias for :meth:`get_cloud_emissions_rows`.

        This used to return a ``pandas.DataFrame``. pandas is no longer a
        default dependency, and returning one type or the other depending on
        whether it happens to be installed would make the return type of a
        public method depend on the environment, so it always returns rows now.
        """
        _deprecated_rows_accessor(
            "get_cloud_emissions_data", "get_cloud_emissions_rows"
        )
        return self.get_cloud_emissions_rows()

    def find_cloud_region(self, provider: str, region: str) -> dict[str, Any] | None:
        """
        Returns the cloud impact row for a provider/region pair, or None.
        """
        return next(
            (
                row
                for row in self.get_cloud_emissions_rows()
                if row["provider"] == provider and row["region"] == region
            ),
            None,
        )

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
        Data is loaded on first access and cached for all tracker instances.
        """
        _ensure_static_data_loaded()
        return _CACHE["carbon_intensity_per_source"]

    def get_cpu_power_rows(self) -> list[dict[str, Any]]:
        """
        Returns CPU power Data, as one dict per row.
        Data is loaded on first access and cached for all tracker instances.
        """
        _ensure_static_data_loaded()
        return _CACHE["cpu_power"]

    def get_cpu_power_data(self) -> list[dict[str, Any]]:
        """
        Deprecated alias for :meth:`get_cpu_power_rows`. See
        :meth:`get_cloud_emissions_data` for why it no longer returns a
        ``pandas.DataFrame``.
        """
        _deprecated_rows_accessor("get_cpu_power_data", "get_cpu_power_rows")
        return self.get_cpu_power_rows()

    def get_nordic_country_energy_mix_data(self) -> Dict:
        """
        Returns Nordic Country Energy Mix Data.
        Data is loaded on first access and cached for all tracker instances.
        """
        _ensure_static_data_loaded()
        return _CACHE["nordic_country_energy_mix"]


class DataSourceException(Exception):
    pass
