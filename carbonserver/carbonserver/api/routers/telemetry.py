"""API router for handling telemetry data in the CarbonServer API."""

import time
from collections import defaultdict, deque
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status

from carbonserver.api.schemas_telemetry import TelemetryCreate
from carbonserver.api.services.telemetry_service import TelemetryService
from carbonserver.container import ServerContainer

TELEMETRY_ROUTER_TAGS = ["Telemetry"]

#: Accepted requests per client IP per window. The SDK sends once per process.
RATE_LIMIT = 60
RATE_WINDOW_SECONDS = 60.0
#: Forget every IP once this many are tracked, so memory stays bounded.
MAX_TRACKED_IPS = 10_000

# ponytail: in-memory, per-process limit. With more than one API instance or
# worker, each keeps its own counts; move to a proxy or Redis limit then.
_recent_requests: dict[str, deque] = defaultdict(deque)

router = APIRouter()


def _rate_limited(host: str) -> bool:
    now = time.monotonic()
    if host not in _recent_requests and len(_recent_requests) >= MAX_TRACKED_IPS:
        _recent_requests.clear()
    hits = _recent_requests[host]
    while hits and now - hits[0] > RATE_WINDOW_SECONDS:
        hits.popleft()
    if len(hits) >= RATE_LIMIT:
        return True
    hits.append(now)
    return False


@router.post(
    "/telemetry",
    tags=TELEMETRY_ROUTER_TAGS,
    status_code=status.HTTP_201_CREATED,
    response_model=UUID,
)
@inject
def add_telemetry(
    telemetry: TelemetryCreate,
    request: Request,
    telemetry_service: TelemetryService = Depends(
        Provide[ServerContainer.telemetry_service]
    ),
) -> UUID:
    host = request.client.host if request.client else "unknown"
    if _rate_limited(host):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many telemetry requests",
        )
    return telemetry_service.add_telemetry(telemetry)
