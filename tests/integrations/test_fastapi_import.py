"""Import surface for the optional FastAPI integration package."""

import builtins
import importlib
import sys

import pytest


def test_fastapi_integration_importable() -> None:
    """Public helpers are importable without instantiating middleware."""
    from codecarbon.integrations.fastapi import (
        CodeCarbonMiddleware,
        add_codecarbon_middleware,
        create_codecarbon_lifespan,
    )

    assert CodeCarbonMiddleware is not None
    assert callable(add_codecarbon_middleware)
    assert callable(create_codecarbon_lifespan)


def test_missing_starlette_shows_helpful_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Middleware import surfaces an actionable hint without Starlette/FastAPI."""
    for key in list(sys.modules):
        if key.startswith("starlette") or key.startswith("codecarbon.integrations.fastapi"):
            del sys.modules[key]

    real_import = builtins.__import__

    def mock_import(
        name: str,
        globals: dict | None = None,
        locals: dict | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ):
        root = name.split(".", 1)[0]
        if root in ("starlette", "fastapi"):
            raise ImportError("no starlette")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    with pytest.raises(ImportError, match=r"pip install .*codecarbon\[fastapi\]"):
        importlib.import_module("codecarbon.integrations.fastapi.middleware")
