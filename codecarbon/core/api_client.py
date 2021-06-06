"""

Based on https://kernelpanic.io/the-modern-way-to-call-apis-in-python

TODO : use async call to API
"""
# from httpx import AsyncClient
import dataclasses
import json
import time
from datetime import datetime

import requests

from codecarbon.core.schemas import EmissionCreate, RunCreate
from codecarbon.external.logger import logger

# from codecarbon.output import EmissionsData


class ApiClient:  # (AsyncClient)
    """
    This class call the Code Carbon API
    Note : The project, team and organization must have been created in the interface.
    """

    run_id = None
    _previous_call = time.time()

    def __init__(self, experiment_id, endpoint_url, api_key):
        """
        :project_id: ID of the existing project
        :api_ley: Code Carbon API_KEY
        """
        # super().__init__(base_url=endpoint_url) # (AsyncClient)
        self.url = endpoint_url
        self.experiment_id = experiment_id
        self.api_key = api_key
        self._create_run(self.experiment_id)

    def add_emission(self, carbon_emission: dict):
        self._previous_call = time.time()
        if self.run_id is None:
            # TODO : raise an Exception ?
            logger.error(
                "add_emissionadd_emission need a run_id : the initial call may have failed. Retrying..."
            )
            self._create_run(self.experiment_id)
        if carbon_emission["duration"] < 1:
            logger.warning(
                "Warning : emission not send because of a duration smaller than 1."
            )
            return False
        emission = EmissionCreate(
            timestamp=datetime.now().isoformat(),
            run_id=self.run_id,
            duration=int(carbon_emission["duration"]),
            emissions=carbon_emission["emissions"],
            energy_consumed=carbon_emission["energy_consumed"],
        )
        try:
            payload = dataclasses.asdict(emission)
            r = requests.put(url=self.url + "/emission", json=payload)
            if r.status_code != 201:
                self._log_error(payload, r)
            assert r.status_code == 201
        except Exception as e:
            logger.error(e, exc_info=True)
            return False
        return True

    def _create_run(self, experiment_id):
        """
        Create the experiment for project_id
        # TODO : Allow to give an existing experiment_id
        """
        try:
            run = RunCreate(
                timestamp=datetime.now().isoformat(), experiment_id=experiment_id
            )
            payload = dataclasses.asdict(run)
            r = requests.put(url=self.url + "/run", json=payload)
            if r.status_code != 200:
                self._log_error(payload, r)
            assert r.status_code == 200
            self.run_id = r.json()["id"]
        except Exception as e:
            logger.error(e, exc_info=True)

    def _log_error(self, payload, response):
        logger.error(f" Error when calling the API with : {json.dumps(payload)}")
        logger.error(
            f" API return http code {response.status_code} and answer : {response.json()}"
        )

    async def close_experiment(self):
        """
        Tell the API that the experiment has ended.
        """
        pass
