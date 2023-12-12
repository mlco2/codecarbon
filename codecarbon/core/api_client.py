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

from codecarbon.core.schemas import (
    EmissionCreate,
    ExperimentCreate,
    OrganizationCreate,
    ProjectCreate,
    RunCreate,
    TeamCreate,
)
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
        self,
        endpoint_url="https://api.codecarbon.io",
        experiment_id=None,
        api_key=None,
        conf=None,
    ):
        """
        :project_id: ID of the existing project
        :api_ley: Code Carbon API_KEY
        """
        # super().__init__(base_url=endpoint_url) # (AsyncClient)
        self.url = endpoint_url
        self.experiment_id = experiment_id
        self.api_key = api_key
        self.conf = conf
        if self.experiment_id is not None:
            self._create_run(self.experiment_id)

    def get_list_organizations(self):
        """
        List all organizations
        """
        url = self.url + "/organizations"
        r = requests.get(url=url, timeout=2)
        if r.status_code != 200:
            self._log_error(url, {}, r)
            return None
        return r.json()

    def create_organization(self, organization: OrganizationCreate):
        """
        Create an organization
        """
        payload = dataclasses.asdict(organization)
        url = self.url + "/organization"
        r = requests.post(url=url, json=payload, timeout=2)
        if r.status_code != 201:
            self._log_error(url, payload, r)
            return None
        return r.json()

    def get_organization(self, organization_id):
        """
        Get an organization
        """
        url = self.url + "/organization/" + organization_id
        r = requests.get(url=url, timeout=2)
        if r.status_code != 200:
            self._log_error(url, {}, r)
            return None
        return r.json()

    def list_teams_from_organization(self, organization_id):
        """
        List all teams
        """
        url = (
            self.url + "/teams/organization/" + organization_id
        )  # TODO : check if this is the right url
        r = requests.get(url=url, timeout=2)
        if r.status_code != 200:
            self._log_error(url, {}, r)
            return None
        return r.json()

    def create_team(self, team: TeamCreate):
        """
        Create a team
        """
        payload = dataclasses.asdict(team)
        url = self.url + "/team"
        r = requests.post(url=url, json=payload, timeout=2)
        if r.status_code != 201:
            self._log_error(url, payload, r)
            return None
        return r.json()

    def list_projects_from_team(self, team_id):
        """
        List all projects
        """
        url = self.url + "/projects/team/" + team_id
        r = requests.get(url=url, timeout=2)
        if r.status_code != 200:
            self._log_error(url, {}, r)
            return None
        return r.json()

    def create_project(self, project: ProjectCreate):
        """
        Create a project
        """
        payload = dataclasses.asdict(project)
        url = self.url + "/project"
        r = requests.post(url=url, json=payload, timeout=2)
        if r.status_code != 201:
            self._log_error(url, payload, r)
            return None
        return r.json()

    def add_emission(self, carbon_emission: dict):
        assert self.experiment_id is not None
        self._previous_call = time.time()
        if self.run_id is None:
            # TODO : raise an Exception ?
            logger.debug(
                "ApiClient.add_emission need a run_id : the initial call may "
                + "have failed. Retrying..."
            )
            self._create_run(self.experiment_id)
            if self.run_id is None:
                logger.error(
                    "ApiClient.add_emission still no run_id, aborting for this time !"
                )
            return False
        if carbon_emission["duration"] < 1:
            logger.warning(
                "ApiClient : emissions not sent because of a duration smaller than 1."
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
            if r.status_code != 201:
                self._log_error(url, payload, r)
                return False
            logger.debug(f"ApiClient - Successful upload emission {payload} to {url}")
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
            logger.error("ApiClient FATAL The API _create_run needs an experiment_id !")
            return None
        try:
            run = RunCreate(
                timestamp=get_datetime_with_timezone(),
                experiment_id=experiment_id,
                os=self.conf.get("os"),
                python_version=self.conf.get("python_version"),
                codecarbon_version=self.conf.get("codecarbon_version"),
                cpu_count=self.conf.get("cpu_count"),
                cpu_model=self.conf.get("cpu_model"),
                gpu_count=self.conf.get("gpu_count"),
                gpu_model=self.conf.get("gpu_model"),
                # Reduce precision for Privacy
                longitude=round(self.conf.get("longitude"), 1),
                latitude=round(self.conf.get("latitude"), 1),
                region=self.conf.get("region"),
                provider=self.conf.get("provider"),
                ram_total_size=self.conf.get("ram_total_size"),
                tracking_mode=self.conf.get("tracking_mode"),
            )
            payload = dataclasses.asdict(run)
            url = self.url + "/run"
            r = requests.post(url=url, json=payload, timeout=2)
            if r.status_code != 201:
                self._log_error(url, payload, r)
                return None
            self.run_id = r.json()["id"]
            logger.info(
                "ApiClient Successfully registered your run on the API.\n\n"
                + f"Run ID: {self.run_id}\n"
                + f"Experiment ID: {self.experiment_id}\n"
            )
            return self.run_id
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Failed to connect to API, please check the configuration. {e}",
                exc_info=False,
            )
        except Exception as e:
            logger.error(e, exc_info=True)

    def list_experiments_from_project(self, project_id: str):
        """
        List all experiments for a project
        """
        url = self.url + "/experiments/project/" + project_id
        r = requests.get(url=url, timeout=2)
        if r.status_code != 200:
            self._log_error(url, {}, r)
            return None
        return r.json()

    def set_experiment(self, experiment_id: str):
        """
        Set the experiment id
        """
        self.experiment_id = experiment_id

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
        if len(payload) > 0:
            logger.error(
                f"ApiClient Error when calling the API on {url} with : {json.dumps(payload)}"
            )
        else:
            logger.error(f"ApiClient Error when calling the API on {url}")
        logger.error(
            f"ApiClient API return http code {response.status_code} and answer : {response.text}"
        )

    def close_experiment(self):
        """
        Tell the API that the experiment has ended.
        """


class simple_utc(tzinfo):
    def tzname(self, **kwargs):
        return "UTC"

    def utcoffset(self, dt):
        return timedelta(0)
