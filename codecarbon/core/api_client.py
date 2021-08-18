"""

Based on https://kernelpanic.io/the-modern-way-to-call-apis-in-python

TODO : use async call to API
"""
# from httpx import AsyncClient
import dataclasses
import json
import time
from datetime import timedelta, tzinfo

import arrow
import requests

from codecarbon.core.schemas import EmissionCreate, ExperimentCreate, RunCreate
from codecarbon.external.logger import logger

# from codecarbon.output import EmissionsData


def get_datetime_with_timezone():
    timestamp = str(arrow.now().isoformat())
    return timestamp


class ApiClient:  # (AsyncClient)
    """
    This class call the Code Carbon API
    Note : The project, team and organization must have been created in the interface.
    """

    run_id = None
    _previous_call = time.time()

    def __init__(
        self, endpoint_url="https://api.codecarbon.io", experiment_id=None, api_key=None
    ):
        """
        :project_id: ID of the existing project
        :api_ley: Code Carbon API_KEY
        """
        # super().__init__(base_url=endpoint_url) # (AsyncClient)
        self.url = endpoint_url
        self.experiment_id = experiment_id
        self.api_key = api_key
        if self.experiment_id is not None:
            self._create_run(self.experiment_id)

    def add_emission(self, carbon_emission: dict):
        assert self.experiment_id is not None
        self._previous_call = time.time()
        if self.run_id is None:
            # TODO : raise an Exception ?
            logger.error(
                "add_emissionadd_emission need a run_id : the initial call may "
                + "have failed. Retrying..."
            )
            self._create_run(self.experiment_id)
        if carbon_emission["duration"] < 1:
            logger.warning(
                "Warning : emission not send because of a duration smaller than 1."
            )
            return False
        emission = EmissionCreate(
            timestamp=get_datetime_with_timezone(),
            run_id=self.run_id,
            duration=int(carbon_emission["duration"]),
            emissions_sum=carbon_emission["emissions"],
            emissions_rate=carbon_emission["emissions_rate"],
            cpu_power=carbon_emission["cpu_power"],
            gpu_power=carbon_emission["gpu_power"],
            ram_power=carbon_emission["ram_power"],
            cpu_energy=carbon_emission["cpu_energy"],
            gpu_energy=carbon_emission["gpu_energy"],
            ram_energy=carbon_emission["ram_energy"],
            energy_consumed=carbon_emission["energy_consumed"],
        )
        try:
            payload = dataclasses.asdict(emission)
            url = self.url + "/emission"
            r = requests.post(url=url, json=payload, timeout=2)
            logger.debug(f"Successful upload emission {payload} to {url}")
            if r.status_code != 201:
                self._log_error(url, payload, r)
                return False
        except Exception as e:
            logger.error(e, exc_info=True)
            return False
        return True

    def _create_run(self, experiment_id):
        """
        Create the experiment for project_id
        # TODO : Allow to give an existing experiment_id
        """
        if self.experiment_id is None:
            # TODO : raise an Exception ?
            logger.error("FATAL The API _create_run need an experiment_id !")
            return None
        try:
            run = RunCreate(
                timestamp=get_datetime_with_timezone(), experiment_id=experiment_id
            )
            payload = dataclasses.asdict(run)
            url = self.url + "/run"
            r = requests.post(url=url, json=payload, timeout=2)
            if r.status_code != 201:
                self._log_error(url, payload, r)
                return None
            self.run_id = r.json()["id"]
            logger.info(
                "Successfully registered your run on the API.\n\n"
                + f"Run ID: {self.run_id}\n"
                + f"Experiment ID: {self.experiment_id}\n"
            )
            return self.run_id
        except Exception as e:
            logger.error(e, exc_info=True)

    def add_experiment(self, experiment: ExperimentCreate):
        """
        Create an experiment, used by the CLI, not the package.
        ::experiment:: The experiment to create.
        """
        payload = dataclasses.asdict(experiment)
        url = self.url + "/experiment"
        r = requests.post(url=url, json=payload, timeout=2)
        if r.status_code != 201:
            self._log_error(url, payload, r)
            return None
        self.experiment_id = r.json()["id"]
        return self.experiment_id

    def _log_error(self, url, payload, response):
        logger.error(
            f" Error when calling the API on {url} with : {json.dumps(payload)}"
        )
        logger.error(
            f" API return http code {response.status_code} and answer : {response.text}"
        )

    def close_experiment(self):
        """
        Tell the API that the experiment has ended.
        """
        pass


class simple_utc(tzinfo):
    def tzname(self, **kwargs):
        return "UTC"

    def utcoffset(self, dt):
        return timedelta(0)
