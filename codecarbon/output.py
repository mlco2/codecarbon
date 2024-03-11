"""
Provides functionality for persistence of data
"""

import csv
import dataclasses
import getpass
import json
import logging
import os
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from typing import List

import pandas as pd
import requests

# from core.schema import EmissionCreate, Emission
from codecarbon.core.api_client import ApiClient
from codecarbon.core.util import backup
from codecarbon.external.logger import logger
from codecarbon.prometheus.prometheus import Prometheus


@dataclass
class EmissionsData:
    """
    Output object containg run data
    """

    timestamp: str
    project_name: str
    run_id: str
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
    cloud_provider: str
    cloud_region: str
    os: str
    python_version: str
    codecarbon_version: str
    cpu_count: float
    cpu_model: str
    gpu_count: float
    gpu_model: str
    longitude: float
    latitude: float
    ram_total_size: float
    tracking_mode: str
    on_cloud: str = "N"
    pue: float = 1

    @property
    def values(self) -> OrderedDict:
        return OrderedDict(self.__dict__.items())

    def compute_delta_emission(self, previous_emission):
        delta_duration = self.duration - previous_emission.duration
        self.duration = delta_duration
        delta_emissions = self.emissions - previous_emission.emissions
        self.emissions = delta_emissions
        self.cpu_energy -= previous_emission.cpu_energy
        self.gpu_energy -= previous_emission.gpu_energy
        self.ram_energy -= previous_emission.ram_energy
        self.energy_consumed -= previous_emission.energy_consumed
        if delta_duration > 0:
            # emissions_rate in g/s : delta_emissions in kg.CO2 / delta_duration in s
            self.emissions_rate = delta_emissions / delta_duration
        else:
            self.emissions_rate = 0

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


@dataclass
class TaskEmissionsData:
    task_name: str
    timestamp: str
    project_name: str
    run_id: str
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
    cloud_provider: str
    cloud_region: str
    os: str
    python_version: str
    codecarbon_version: str
    cpu_count: float
    cpu_model: str
    gpu_count: float
    gpu_model: str
    longitude: float
    latitude: float
    ram_total_size: float
    tracking_mode: str
    on_cloud: str = "N"

    @property
    def values(self) -> OrderedDict:
        return OrderedDict(self.__dict__.items())


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

    def __init__(self, save_file_path: str, on_csv_write: str = "append"):
        if on_csv_write not in {"append", "update"}:
            raise ValueError(
                f"Unknown `on_csv_write` value: {on_csv_write}"
                + " (should be one of 'append' or 'update'"
            )
        self.on_csv_write: str = on_csv_write
        self.save_file_path: str = save_file_path

    def has_valid_headers(self, data: EmissionsData):
        with open(self.save_file_path) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            dict_from_csv = dict(list(csv_reader)[0])
            list_of_column_names = list(dict_from_csv.keys())
            return list(data.values.keys()) == list_of_column_names

    def out(self, data: EmissionsData):
        file_exists: bool = os.path.isfile(self.save_file_path)
        if file_exists and not self.has_valid_headers(data):
            logger.info("Backing up old emission file")
            backup(self.save_file_path)
            file_exists = False

        if not file_exists:
            df = pd.DataFrame(columns=data.values.keys())
            df = pd.concat([df, pd.DataFrame.from_records([dict(data.values)])])
        elif self.on_csv_write == "append":
            df = pd.read_csv(self.save_file_path)
            df = pd.concat([df, pd.DataFrame.from_records([dict(data.values)])])
        else:
            df = pd.read_csv(self.save_file_path)
            df_run = df.loc[df.run_id == data.run_id]
            if len(df_run) < 1:
                df = pd.concat([df, pd.DataFrame.from_records([dict(data.values)])])
            elif len(df_run) > 1:
                logger.warning(
                    f"CSV contains more than 1 ({len(df_run)})"
                    + f" rows with current run ID ({data.run_id})."
                    + "Appending instead of updating."
                )
                df = pd.concat([df, pd.DataFrame.from_records([dict(data.values)])])
            else:
                df.at[df.run_id == data.run_id, data.values.keys()] = (
                    data.values.values()
                )

        df.to_csv(self.save_file_path, index=False)

    def task_out(self, data: List[TaskEmissionsData], experiment_name: str, output_dir):
        run_id = data[0].run_id
        save_task_file_path = os.path.join(
            output_dir, "emissions_" + experiment_name + "_" + run_id + ".csv"
        )
        df = pd.DataFrame(columns=data[0].values.keys())
        df = pd.concat(
            [
                df,
                pd.DataFrame.from_records(
                    [dict(data_point.values) for data_point in data]
                ),
            ]
        )
        df.to_csv(save_task_file_path, index=False)


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

    run_id = None

    def __init__(self, endpoint_url: str, experiment_id: str, api_key: str, conf):
        self.endpoint_url: str = endpoint_url
        self.api = ApiClient(
            experiment_id=experiment_id,
            endpoint_url=endpoint_url,
            api_key=api_key,
            conf=conf,
        )
        self.run_id = self.api.run_id

    def out(self, data: EmissionsData):
        try:
            self.api.add_emission(dataclasses.asdict(data))
        except Exception as e:
            logger.error(e, exc_info=True)


class PrometheusOutput(BaseOutput):
    """
    Send emissions data to prometheus pushgateway
    """

    def __init__(self, prometheus_url: str):
        self.prometheus = Prometheus(prometheus_url)

    def out(self, data: EmissionsData):
        try:
            self.prometheus.add_emission(dataclasses.asdict(data))
        except Exception as e:
            logger.error(e, exc_info=True)


class LoggerOutput(BaseOutput):
    """
    Send emissions data to a logger
    """

    def __init__(self, logger, severity=logging.INFO):
        self.logger = logger
        self.logging_severity = severity

    def out(self, data: EmissionsData):
        try:
            payload = dataclasses.asdict(data)
            self.logger.log(self.logging_severity, msg=json.dumps(payload))
        except Exception as e:
            logger.error(e, exc_info=True)


class GoogleCloudLoggerOutput(LoggerOutput):
    """
    Send emissions data to GCP Cloud Logging
    """

    def out(self, data: EmissionsData):
        try:
            payload = dataclasses.asdict(data)
            self.logger.log_struct(payload, severity=self.logging_severity)
        except Exception as e:
            logger.error(e, exc_info=True)
