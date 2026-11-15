import importlib.util
import logging
from pathlib import Path
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from carbonserver.api.errors import (
    NotAllowedError,
    NotAllowedErrorEnum,
    NotFoundError,
    NotFoundErrorEnum,
    UserException,
)
from carbonserver.config import settings

MAIN_PATH = Path(__file__).parents[3] / "main.py"


def load_main():
    """Import carbonserver/main.py without touching a database."""
    spec = importlib.util.spec_from_file_location("carbonserver_main", MAIN_PATH)
    module = importlib.util.module_from_spec(spec)
    with mock.patch("sqlalchemy.MetaData.create_all"):
        spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def main_module():
    return load_main()


@pytest.mark.parametrize(
    "error, status_code",
    [
        (
            NotAllowedError(
                code=NotAllowedErrorEnum.NOT_IN_ORGANISATION, message="Not allowed"
            ),
            403,
        ),
        (NotFoundError(code=NotFoundErrorEnum.NOT_FOUND, message="Not found"), 404),
    ],
)
def test_user_exception_returns_its_http_status(main_module, error, status_code):
    app = main_module.app

    async def raise_user_exception():
        raise UserException(error)

    path = f"/raise-user-exception-{status_code}"
    app.add_api_route(path, raise_user_exception)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get(path)

    assert response.status_code == status_code
    assert response.json() == {"detail": error.message}


def load_app(monkeypatch, environment, cors_origins=None):
    monkeypatch.setattr(settings, "environment", environment)
    monkeypatch.setattr(settings, "frontend_url", "")
    if cors_origins is None:
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("CORS_ORIGINS", cors_origins)
    return load_main()


def allowed_origin(main, origin):
    """Origin echoed by a CORS preflight request, None when refused."""
    response = TestClient(main.app).options(
        "/",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )
    return response.headers.get("access-control-allow-origin")


@pytest.mark.parametrize("environment", ["local", "develop"])
def test_cors_allows_localhost_in_development(monkeypatch, environment):
    main = load_app(monkeypatch, environment)

    assert allowed_origin(main, "http://localhost:3000") == "http://localhost:3000"


def test_cors_refuses_localhost_in_production(monkeypatch):
    main = load_app(monkeypatch, "production")

    assert allowed_origin(main, "http://localhost:3000") is None
    assert (
        allowed_origin(main, "https://dashboard.codecarbon.io")
        == "https://dashboard.codecarbon.io"
    )


def test_cors_origins_env_var_is_listed_once(monkeypatch):
    main = load_app(
        monkeypatch, "production", " https://a.example , ,https://b.example,"
    )

    origins = main.get_cors_origins()

    assert allowed_origin(main, "https://b.example") == "https://b.example"
    assert origins.count("https://a.example") == 1
    assert "" not in origins


def session_secret_key(main):
    (session,) = [m for m in main.app.user_middleware if m.cls is SessionMiddleware]
    return session.kwargs["secret_key"]


@pytest.mark.parametrize("environment", ["local", "develop"])
def test_session_key_is_stable_in_development(monkeypatch, environment):
    monkeypatch.setattr(settings, "session_secret_key", "")

    first = session_secret_key(load_app(monkeypatch, environment))
    second = session_secret_key(load_app(monkeypatch, environment))

    assert first == second


def test_session_key_uses_configured_secret(monkeypatch):
    monkeypatch.setattr(settings, "session_secret_key", "configured-secret")

    main = load_app(monkeypatch, "production")

    assert session_secret_key(main) == "configured-secret"


def test_missing_session_key_warns_in_production(monkeypatch, caplog):
    monkeypatch.setattr(settings, "session_secret_key", "")

    with caplog.at_level(logging.WARNING, logger="carbonserver"):
        main = load_app(monkeypatch, "production")

    assert len(session_secret_key(main)) == 64
    assert "SESSION_SECRET_KEY is not set" in caplog.text
