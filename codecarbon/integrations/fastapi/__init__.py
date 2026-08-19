"""FastAPI integration: per-request energy attribution middleware."""

from codecarbon.integrations.fastapi.attribution import EnergyAttributor, RequestEnergy
from codecarbon.integrations.fastapi.middleware import (
    CodeCarbonMiddleware,
    add_codecarbon_middleware,
)

__all__ = [
    "CodeCarbonMiddleware",
    "EnergyAttributor",
    "RequestEnergy",
    "add_codecarbon_middleware",
]
