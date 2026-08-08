"""
Submission of benchmark records to a CodeCarbon API.

The server applies the same §6 validity rules the harness already ran locally,
so a rejection here means the two disagree -- normally a version skew between
the harness and the server. Its failure list is surfaced verbatim rather than
summarised, because it is the same list the operator saw locally and comparing
them is how the skew gets diagnosed.
"""

from typing import Any, Dict, Optional

import requests

from codecarbon.external.logger import logger

DEFAULT_TIMEOUT = 60


class UploadError(Exception):
    """A submission was not accepted."""

    def __init__(self, message: str, failures: Optional[list] = None):
        self.failures = failures or []
        super().__init__(message)


def upload_record(
    record: Dict[str, Any],
    endpoint_url: str,
    api_token: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    POST one BoAmps benchmark record and return the id the server assigned.

    Args:
        record: The BoAmps record to submit.
        endpoint_url: Base URL of the API, or the full /model-benchmarks URL.
        api_token: Bearer token, when the server requires authentication.
        timeout: Request timeout in seconds.

    Returns:
        The identifier assigned by the server.
    """
    url = endpoint_url.rstrip("/")
    if not url.endswith("/model-benchmarks"):
        url = f"{url}/model-benchmarks"

    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    response = requests.post(url, json=record, headers=headers, timeout=timeout)

    if response.status_code == 201:
        benchmark_id = response.json()
        logger.info("Benchmark submitted: %s", benchmark_id)
        return benchmark_id

    if response.status_code == 422:
        detail = _detail(response)
        failures = detail.get("failures", []) if isinstance(detail, dict) else []
        raise UploadError(
            "The server rejected the record against the benchmark spec. The "
            "harness runs the same rules locally, so a rejection here usually "
            "means the harness and the server are on different versions.",
            failures=failures,
        )

    if response.status_code in (401, 403):
        raise UploadError(
            f"Not authorised to submit ({response.status_code}). Pass --api-token, "
            "or check the server's auth configuration."
        )

    raise UploadError(
        f"Unexpected response {response.status_code}: {response.text[:500]}"
    )


def _detail(response: requests.Response) -> Any:
    try:
        return response.json().get("detail")
    except (ValueError, AttributeError):
        return None
