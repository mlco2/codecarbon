"""FastAPI integration: middleware and lifespan helpers."""

from codecarbon.integrations.fastapi.lifespan import create_codecarbon_lifespan
from codecarbon.integrations.fastapi.middleware import (
    CodeCarbonMiddleware,
    add_codecarbon_middleware,
    log_request_complete,
    shutdown_codecarbon_middleware,
)

__all__ = [
    "CodeCarbonMiddleware",
    "add_codecarbon_middleware",
    "create_codecarbon_lifespan",
    "log_request_complete",
    "shutdown_codecarbon_middleware",
]
