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

import requests

# from core.schema import EmissionCreate, Emission
from codecarbon.core.api_client import ApiClient
from codecarbon.external.logger import logger


@dataclass
class EmissionsData:
    """
    Output object containg experiment data
    # TODO : Replace by a pdantic BaseModel ?
    """

    timestamp: str
    project_name: str
    duration: float
    emissions: float
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


class BaseOutput(ABC):
    """
    An abstract class that requires children to inherit a single method,
    `out` which is used for persisting data. This could be by saving it to a file,
    posting to Json Box, saving to a database, sending a slack message etc.
    """

    @abstractmethod
    def out(self, data: EmissionsData):
        pass


class FileOutput(BaseOutput):
    """
    Saves experiment artifacts to a file
    """

    def __init__(self, save_file_path: str):
        self.save_file_path: str = save_file_path

    def out(self, data: EmissionsData):
        file_exists: bool = os.path.isfile(self.save_file_path)

        with open(self.save_file_path, "a+") as f:
            writer = csv.DictWriter(f, fieldnames=data.values.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data.values)


class HTTPOutput(BaseOutput):
    """
    Send emissions data to HTTP endpoint
    Warning : This is an empty model to guide you.
    We do not provide a server.
    """

    def __init__(self, endpoint_url: str):
        self.endpoint_url: str = endpoint_url

    def out(self, data: EmissionsData):
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

    def out(self, data: EmissionsData):
        try:
            self.api.add_emission(dataclasses.asdict(data))
        except Exception as e:
            logger.error(e, exc_info=True)
