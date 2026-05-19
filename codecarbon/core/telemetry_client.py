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
        endpoint_url: str = "https://api.codecarbon.io",
        telemetry: Optional[Union[TelemetryCreate, dict]] = None,
        api_key: Optional[str] = None,
    ):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.telemetry_url = self.endpoint_url + "/telemetry"
        self.api_key = api_key
        self.headers = self._build_headers(api_key)
        self.telemetry = self._validate_telemetry(telemetry) if telemetry else None

    @staticmethod
    def _build_headers(api_key: Optional[str]) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["x-api-token"] = api_key
        return headers

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
            if response.status_code == 404:
                logger.warning(
                    "Telemetry API not found at %s (HTTP 404); Tier 1 not recorded.",
                    self.telemetry_url,
                )
                return None
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
