import requests

from codecarbon.core.telemetry_schemas import TelemetryCreate
from codecarbon.external.logger import logger


def post_private_telemetry(url: str, payload: dict, api_key: str | None) -> bool:
    """POST a private telemetry payload to ``/telemetry``.

    Args:
        url: API base URL.
        payload: Telemetry fields dict.
        api_key: Optional API token.

    Returns:
        True if the server accepted the payload (HTTP 201).
    """
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-token"] = api_key
    body = TelemetryCreate(**payload).model_dump(mode="json", exclude_none=True)
    telemetry_url = f"{url.rstrip('/')}/telemetry"
    try:
        response = requests.post(
            url=telemetry_url,
            json=body,
            headers=headers,
            timeout=2,
        )
    except Exception:
        logger.error("Telemetry request failed.", exc_info=True)
        return False
    if response.status_code == 201:
        return True
    if response.status_code == 404:
        logger.warning(
            "Telemetry API not found at %s (HTTP 404); Tier 1 not recorded.",
            telemetry_url,
        )
    else:
        logger.error(
            "Telemetry API %s: %s",
            response.status_code,
            response.text,
        )
        logger.debug("Telemetry request body: %s", body)
    return False
