import json
from typing import Optional, Union

import requests

from codecarbon.core.telemetry_schemas import TelemetryCreate
from codecarbon.external.logger import logger


class TelemetryClient:
    """
    Client dedicated to sending CodeCarbon telemetry payloads.
    """

    def __init__(
        self,
        endpoint_url="https://api.codecarbon.io",
        telemetry: Optional[Union[TelemetryCreate, dict]] = None,
    ):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.telemetry_url = self.endpoint_url + "/telemetry"
        self.headers = {"Content-Type": "application/json"}
        self.telemetry = self._validate_telemetry(telemetry) if telemetry else None

    def add_telemetry(self, telemetry: Optional[Union[TelemetryCreate, dict]] = None):
        telemetry_payload = (
            self._validate_telemetry(telemetry) if telemetry else self.telemetry
        )
        if telemetry_payload is None:
            logger.error("TelemetryClient.add_telemetry() needs a telemetry payload")
            return None
        payload = telemetry_payload.model_dump(mode="json", exclude_none=True)

        try:
            response = requests.post(
                url=self.telemetry_url,
                json=payload,
                timeout=2,
                headers=self.headers,
            )
            if response.status_code != 201:
                self._log_error(payload, response)
                return None
            return response.json()
        except Exception as e:
            logger.error(e, exc_info=True)
            return None

    @staticmethod
    def _validate_telemetry(telemetry: Union[TelemetryCreate, dict]) -> TelemetryCreate:
        if isinstance(telemetry, TelemetryCreate):
            return telemetry
        return TelemetryCreate(**telemetry)

    def _log_error(self, payload, response):
        logger.error(
            f"TelemetryClient Error when calling the API on {self.telemetry_url} with : {json.dumps(payload)}"
        )
        logger.error(
            f"TelemetryClient API return http code {response.status_code} and answer : {response.text}"
        )
