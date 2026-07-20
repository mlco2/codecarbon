"""FastAPI integration: middleware and lifespan helpers."""

try:
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
    "add_codecarbon_middleware",
    "compose_lifespans",
    "create_codecarbon_lifespan",
    "log_request_complete",
    "shutdown_codecarbon_middleware",
]
