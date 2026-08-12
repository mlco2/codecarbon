"""FastAPI integration: middleware and lifespan helpers."""

try:
    from codecarbon.integrations.fastapi.attribution import (
        EndpointEnergy,
        EnergyAttributor,
        RequestEnergy,
        install_cpu_accounting,
    )
    from codecarbon.integrations.fastapi.lifespan import (
        compose_lifespans,
        create_codecarbon_lifespan,
    )
    from codecarbon.integrations.fastapi.middleware import (
        CodeCarbonMiddleware,
        add_codecarbon_middleware,
        log_request_complete,
        shutdown_codecarbon_middleware,
    )
except ImportError as exc:
    raise ImportError(
        "CodeCarbon FastAPI integration requires Starlette (installed with FastAPI). "
        "Install optional dependencies with: pip install 'codecarbon[fastapi]'"
    ) from exc

__all__ = [
    "CodeCarbonMiddleware",
    "EndpointEnergy",
    "EnergyAttributor",
    "RequestEnergy",
    "add_codecarbon_middleware",
    "compose_lifespans",
    "create_codecarbon_lifespan",
    "install_cpu_accounting",
    "log_request_complete",
    "shutdown_codecarbon_middleware",
]
