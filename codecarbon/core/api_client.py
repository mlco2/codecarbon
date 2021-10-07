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
        self.token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJPZ20tY1F6bjVzazFzWm1ra2R3ZkFmWnpGWmNGaHlfNDlIR3V4MWcydlBNIn0.eyJleHAiOjE2MzA1MDE2NDUsImlhdCI6MTYzMDUwMTU4NSwianRpIjoiMDhlNDZlOWMtMDRmZC00ZjQ5LWEyZTEtNjQxODgyYTg5ZDNiIiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo4MDgwL2F1dGgvcmVhbG1zL21hc3RlciIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiIxYjJlNTkwZi1iYzkxLTQxYzAtYmQ4OS03ZTk3OTU1MDQxMmUiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJiYWNrZW5kIiwic2Vzc2lvbl9zdGF0ZSI6IjYyNDk4MWE3LTA1OTItNDgzNy05ZGNmLTFmZjUwMTMyOTE4NSIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsiZGVmYXVsdC1yb2xlcy1tYXN0ZXIiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJlbWFpbCBwcm9maWxlIiwic2lkIjoiNjI0OTgxYTctMDU5Mi00ODM3LTlkY2YtMWZmNTAxMzI5MTg1IiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInByZWZlcnJlZF91c2VybmFtZSI6InRlc3QifQ.JVLK9XhWAzveC94QCtIeMUK55WP8rAa65ZbRAKTJHl_Hm_0xSGzhdz7XnP2YSwKdilQtFSP9-m_YfANzOYIoBX5jYrLq-noUkYiXCh7szMqj9bdRnTLL96SGbIYK3TEPCmRH3SocIeOwTwUmt7fatX9Q1QKpXqvzHfRjVmOnr_wI1VhyHhOFPcxH1UWgDoA52SL9c19z5O10lI4laiseFdzMIXLieCaJdqT2OVfOao63WSasPDL4f4OId62rQpxXmwdpxLZid4QyPsTfqwJCqa1kolbjoveaiBovckBjaz7_ix23PGMfzc3OXqs3Q5v9ysLXJmh27ZK8DkjL3VQIEw"
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
            r = requests.post(
                url=url,
                json=payload,
                timeout=2,
                headers={
                    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJPZ20tY1F6bjVzazFzWm1ra2R3ZkFmWnpGWmNGaHlfNDlIR3V4MWcydlBNIn0.eyJleHAiOjE2MzA1MDE2NDUsImlhdCI6MTYzMDUwMTU4NSwianRpIjoiMDhlNDZlOWMtMDRmZC00ZjQ5LWEyZTEtNjQxODgyYTg5ZDNiIiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo4MDgwL2F1dGgvcmVhbG1zL21hc3RlciIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiIxYjJlNTkwZi1iYzkxLTQxYzAtYmQ4OS03ZTk3OTU1MDQxMmUiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJiYWNrZW5kIiwic2Vzc2lvbl9zdGF0ZSI6IjYyNDk4MWE3LTA1OTItNDgzNy05ZGNmLTFmZjUwMTMyOTE4NSIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsiZGVmYXVsdC1yb2xlcy1tYXN0ZXIiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJlbWFpbCBwcm9maWxlIiwic2lkIjoiNjI0OTgxYTctMDU5Mi00ODM3LTlkY2YtMWZmNTAxMzI5MTg1IiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInByZWZlcnJlZF91c2VybmFtZSI6InRlc3QifQ.JVLK9XhWAzveC94QCtIeMUK55WP8rAa65ZbRAKTJHl_Hm_0xSGzhdz7XnP2YSwKdilQtFSP9-m_YfANzOYIoBX5jYrLq-noUkYiXCh7szMqj9bdRnTLL96SGbIYK3TEPCmRH3SocIeOwTwUmt7fatX9Q1QKpXqvzHfRjVmOnr_wI1VhyHhOFPcxH1UWgDoA52SL9c19z5O10lI4laiseFdzMIXLieCaJdqT2OVfOao63WSasPDL4f4OId62rQpxXmwdpxLZid4QyPsTfqwJCqa1kolbjoveaiBovckBjaz7_ix23PGMfzc3OXqs3Q5v9ysLXJmh27ZK8DkjL3VQIEw"
                },
            )
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
