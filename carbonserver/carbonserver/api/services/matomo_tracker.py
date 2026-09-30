import logging
import secrets
import threading
from typing import Optional

import httpx

LOGGER = logging.getLogger(__name__)


class MatomoTracker:
    """Send events to Matomo's HTTP Tracking API for things the browser cannot
    see, such as the account being created on the API side.

    Events carry a category, an action and an optional name, and nothing that
    identifies a person: the visitor id is random per event, so they only
    count occurrences. Sending is best effort and never blocks or fails the
    request that triggered it. Without a URL and site id it does nothing.
    """

    def __init__(self, url: str = "", site_id: str = "") -> None:
        self._endpoint = f"{url.rstrip('/')}/matomo.php" if url else ""
        self._site_id = site_id

    @property
    def enabled(self) -> bool:
        return bool(self._endpoint and self._site_id)

    def track_event(
        self, category: str, action: str, name: Optional[str] = None
    ) -> None:
        if not self.enabled:
            return
        params = {
            "idsite": self._site_id,
            "rec": "1",
            "apiv": "1",
            "e_c": category,
            "e_a": action,
            "_id": secrets.token_hex(8),
            "rand": secrets.token_hex(4),
        }
        if name:
            params["e_n"] = name
        threading.Thread(target=self._send, args=(params,), daemon=True).start()

    def _send(self, params: dict) -> None:
        try:
            httpx.get(self._endpoint, params=params, timeout=3.0)
        except httpx.HTTPError as error:
            LOGGER.debug("Matomo event not sent: %s", error)
