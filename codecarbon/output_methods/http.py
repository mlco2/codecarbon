import dataclasses
import getpass

from codecarbon.core.api_client import ApiClient, get_http_session
from codecarbon.external.logger import logger
from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData


class HTTPOutput(BaseOutput):
    """
    Send emissions data to HTTP endpoint
    Warning : This is an empty model to guide you.
    We do not provide a server.
    """

    def __init__(self, endpoint_url: str):
        self.endpoint_url: str = endpoint_url
        self._session = get_http_session(endpoint_url)

    def out(self, total: EmissionsData, _: EmissionsData):
        try:
            payload = dataclasses.asdict(total)
            payload["user"] = getpass.getuser()
            resp = self._session.post(self.endpoint_url, json=payload, timeout=10)
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

    def __init__(
        self,
        endpoint_url: str,
        experiment_id: str,
        api_key: str,
        conf,
    ):
        self.endpoint_url: str = endpoint_url
        self.api = ApiClient(
            experiment_id=experiment_id,
            endpoint_url=endpoint_url,
            api_key=api_key,
            conf=conf,
            create_run_automatically=False,
        )
        self.run_id = self.api.run_id

    def _ensure_api_run(self) -> None:
        if self.api.run_id is None and self.api.experiment_id is not None:
            self.api._create_run(self.api.experiment_id)
            self.run_id = self.api.run_id

    def live_out(self, _, delta: EmissionsData):
        # Called at regular intervals
        try:
            self._ensure_api_run()
            self.api.add_emission(dataclasses.asdict(delta))
        except Exception as e:
            logger.error(e, exc_info=True)

    def out(self, _, delta: EmissionsData):
        # Called on exit
        try:
            self._ensure_api_run()
            self.api.add_emission(dataclasses.asdict(delta))
        except Exception as e:
            logger.error(e, exc_info=True)
