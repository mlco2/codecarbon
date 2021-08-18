"""
Provides functionality for persistence of data
"""

import csv
import dataclasses
import getpass
import os
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import requests

# from core.schema import EmissionCreate, Emission
from codecarbon.core.api_client import ApiClient
from codecarbon.external.logger import logger


@dataclass
class EmissionsData:
    """
    Output object containg experiment data
    """

    timestamp: str
    project_name: str
    duration: float
    emissions: float
    emissions_rate: float
    cpu_power: float
    gpu_power: float
    ram_power: float
    cpu_energy: float
    gpu_energy: float
    ram_energy: float
    energy_consumed: float
    country_name: str
    country_iso_code: str
    region: str
    on_cloud: str = "N"
    cloud_provider: str = ""
    cloud_region: str = ""

    @property
    def values(self) -> OrderedDict:
        return OrderedDict(self.__dict__.items())

    def substract_in_place(self, previous_emission):
        self.duration = self.duration - previous_emission.duration
        self.emissions = self.emissions - previous_emission.emissions
        self.energy_consumed = self.energy_consumed - previous_emission.energy_consumed
        self.emissions_rate = (self.emissions * 1000 / self.duration,)

    def compute_emissions_rate(self, previous_emission):
        delta_duration = self.duration - previous_emission.duration
        delta_emissions = self.emissions - previous_emission.emissions
        # delta_emissions in Kg.CO2/s * 1000 / duration in seconds = g.CO2/s
        if delta_duration > 0:
            self.emissions_rate = delta_emissions * 1000 / delta_duration
        else:
            self.emissions_rate = 0


class BaseOutput(ABC):
    """
    An abstract class that requires children to inherit a single method,
    `out` which is used for persisting data. This could be by saving it to a file,
    posting to Json Box, saving to a database, sending a slack message etc.
    """

    @abstractmethod
    def out(self, data: EmissionsData, previous_data: Optional[EmissionsData] = None):
        pass


class FileOutput(BaseOutput):
    """
    Saves experiment artifacts to a file
    """

    def __init__(self, save_file_path: str):
        self.save_file_path: str = save_file_path

    def has_valid_headers(self, data: EmissionsData):
        with open(self.save_file_path) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            dict_from_csv = dict(list(csv_reader)[0])
            list_of_column_names = list(dict_from_csv.keys())
            return list(data.values.keys()) == list_of_column_names

    def out(self, data: EmissionsData, previous_data: Optional[EmissionsData] = None):
        file_exists: bool = os.path.isfile(self.save_file_path)
        if file_exists and not self.has_valid_headers(data):
            logger.info("Backing up old emission file")
            new_name = self.save_file_path + ".bak"
            idx = 1
            while os.path.isfile(new_name):
                new_name = self.save_file_path + f"_{idx}.bak"
                idx += 1
            os.rename(self.save_file_path, new_name)
            file_exists = False

        if not file_exists:
            df = pd.DataFrame(columns=data.values.keys())
        else:
            df = pd.read_csv(self.save_file_path)

        if previous_data is None:
            df = df.append(dict(data.values), ignore_index=True)
            logger.info("Appending emissions data to {}".format(self.save_file_path))
        else:
            loc = (df.timestamp == previous_data.timestamp) & (
                df.project_name == previous_data.project_name
            )
            if len(df.loc[loc]) < 1:
                message = (
                    "Looking for ({}, {}) in previous emissions data (tracker was"
                    + " re-started) but CodeCarbon could not find a matching emissions "
                    + "line in {}. Appending."
                )
                logger.warning(
                    message.format(
                        previous_data.timestamp,
                        previous_data.project_name,
                        self.save_file_path,
                    )
                )
                df = df.append(dict(data.values), ignore_index=True)
            elif len(df.loc[loc]) > 1:
                message = (
                    "Looking for ({}, {}) in previous emissions data (tracker was"
                    + " re-started) but CodeCarbon found more than 1 matching emissions"
                    + " line in {}. Appending."
                )
                logger.warning(
                    message.format(
                        previous_data.timestamp,
                        previous_data.project_name,
                        self.save_file_path,
                    )
                )
                df = df.append(dict(data.values), ignore_index=True)
            else:
                logger.info(
                    "Updating line ({}, {})".format(
                        previous_data.timestamp, previous_data.project_name
                    )
                )
                df.at[
                    (df.timestamp == previous_data.timestamp)
                    & (df.project_name == previous_data.project_name)
                ] = dict(data.values)

        df.to_csv(self.save_file_path, index=False)


class HTTPOutput(BaseOutput):
    """
    Send emissions data to HTTP endpoint
    Warning : This is an empty model to guide you.
    We do not provide a server.
    """

    def __init__(self, endpoint_url: str):
        self.endpoint_url: str = endpoint_url

    def out(self, data: EmissionsData, previous_data: Optional[EmissionsData] = None):
        try:
            payload = dataclasses.asdict(data)
            payload["user"] = getpass.getuser()
            resp = requests.post(self.endpoint_url, json=payload, timeout=10)
            if resp.status_code != 201:
                logger.warning(
                    "HTTP Output returned an unexpected status code: ",
                    resp,
                )
        except Exception as e:
            logger.error(e, exc_info=True)


class CodeCarbonAPIOutput(BaseOutput):
    """
    Send emissions data to HTTP endpoint
    """

    def __init__(self, endpoint_url: str, experiment_id: str, api_key: str):
        self.endpoint_url: str = endpoint_url
        self.api = ApiClient(
            experiment_id=experiment_id,
            endpoint_url=endpoint_url,
            api_key=api_key,
        )

    def out(self, data: EmissionsData, previous_data: Optional[EmissionsData] = None):
        try:
            self.api.add_emission(dataclasses.asdict(data))
        except Exception as e:
            logger.error(e, exc_info=True)
