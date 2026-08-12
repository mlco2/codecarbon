"""FastAPI integration: middleware and lifespan helpers."""

try:
    from codecarbon.integrations.fastapi.lifespan import create_codecarbon_lifespan
    from codecarbon.integrations.fastapi.middleware import (
        CodeCarbonMiddleware,
        add_codecarbon_middleware,
        log_request_complete,
        shutdown_codecarbon_middleware,
    )
    from codecarbon.integrations.fastapi.tiers import (
        EndpointTotals,
        MeasurementTier,
        RequestMeasurement,
        TierDetection,
        detect_measurement_tier,
    )
except ImportError as exc:
    raise ImportError(
        "CodeCarbon FastAPI integration requires Starlette (installed with FastAPI). "
        "Install optional dependencies with: pip install 'codecarbon[fastapi]'"
    ) from exc

__all__ = [
    "CodeCarbonMiddleware",
    "EndpointTotals",
    "MeasurementTier",
    "RequestMeasurement",
    "TierDetection",
    "detect_measurement_tier",
    "add_codecarbon_middleware",
    "create_codecarbon_lifespan",
    "log_request_complete",
    "shutdown_codecarbon_middleware",
]
