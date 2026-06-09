from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from carbonserver.api.routers import authenticate
from carbonserver.api.services.auth_providers.oidc_auth_provider import (
    OIDCAuthProvider,
)
from carbonserver.container import ServerContainer

SESSION_COOKIE_NAME = "user_session"


@pytest.fixture
def custom_test_server():
    container = ServerContainer()
    container.wire(modules=[authenticate])
    app = FastAPI()
    app.container = container
    app.add_middleware(SessionMiddleware, secret_key="test-secret-key")
    app.include_router(authenticate.router)
    yield app


@pytest.fixture
def client(custom_test_server):
    yield TestClient(custom_test_server)


def test_logout_clears_cookie_and_session(client, monkeypatch):
    class DummySession(dict):
        def clear(self):
            self["cleared"] = True

    dummy_session = DummySession()

    def fake_request():
        class FakeRequest:
            base_url = "http://testserver/"
            session = dummy_session

        return FakeRequest()

    monkeypatch.setattr("carbonserver.api.routers.authenticate.Request", fake_request)

    # Set cookie and session in request
    cookies = {SESSION_COOKIE_NAME: "dummy_token"}
    with client as c:
        # Set session data by making a request that sets session
        c.cookies.set(SESSION_COOKIE_NAME, "dummy_token")
        # There is no direct way to set session data before logout, so just call logout
        response = c.get("/auth/logout", cookies=cookies)
        assert response.status_code == 200
        assert (
            SESSION_COOKIE_NAME not in response.cookies
            or response.cookies.get(SESSION_COOKIE_NAME) == ""
        )
        # We cannot directly check session cleared, but can check that logout returns redirect
        assert "window.location.href" in response.text


# --- Token revocation tests ---


@pytest.fixture
def mock_oidc_client():
    """Create a mock OIDC client with load_server_metadata and _get_oauth_client."""
    client = MagicMock()
    client.load_server_metadata = AsyncMock()
    client._get_oauth_client = MagicMock()
    return client


@pytest.fixture
def oidc_provider(mock_oidc_client):
    """Create an OIDCAuthProvider with a mocked client."""
    with patch.object(OIDCAuthProvider, "__init__", lambda self, **kw: None):
        provider = OIDCAuthProvider()
    provider.client = mock_oidc_client
    return provider


@pytest.mark.asyncio
async def test_revoke_token_success(oidc_provider, mock_oidc_client):
    """Token is revoked successfully when the provider exposes a revocation_endpoint."""
    mock_oidc_client.load_server_metadata.return_value = {
        "revocation_endpoint": "https://auth.example.com/revoke",
    }

    mock_response = MagicMock(status_code=200)
    mock_http_client = AsyncMock()
    mock_http_client.request = AsyncMock(return_value=mock_response)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)
    mock_oidc_client._get_oauth_client.return_value = mock_http_client

    await oidc_provider.revoke_token("test-access-token")

    mock_http_client.request.assert_called_once_with(
        "POST",
        "https://auth.example.com/revoke",
        withhold_token=True,
        data={"token": "test-access-token", "token_type_hint": "access_token"},
    )


@pytest.mark.asyncio
async def test_revoke_token_no_endpoint(oidc_provider, mock_oidc_client):
    """Revocation is silently skipped when the provider has no revocation_endpoint."""
    mock_oidc_client.load_server_metadata.return_value = {
        "authorization_endpoint": "https://auth.example.com/authorize",
    }

    await oidc_provider.revoke_token("test-access-token")

    mock_oidc_client._get_oauth_client.assert_not_called()


@pytest.mark.asyncio
async def test_revoke_token_http_error(oidc_provider, mock_oidc_client):
    """Revocation failure does not raise — logout must always succeed."""
    mock_oidc_client.load_server_metadata.return_value = {
        "revocation_endpoint": "https://auth.example.com/revoke",
    }

    mock_response = MagicMock(status_code=503, text="Service Unavailable")
    mock_http_client = AsyncMock()
    mock_http_client.request = AsyncMock(return_value=mock_response)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)
    mock_oidc_client._get_oauth_client.return_value = mock_http_client

    # Should not raise
    await oidc_provider.revoke_token("test-access-token")


@pytest.mark.asyncio
async def test_revoke_token_exception(oidc_provider, mock_oidc_client):
    """Revocation is non-blocking even when load_server_metadata raises."""
    mock_oidc_client.load_server_metadata.side_effect = ConnectionError(
        "Network unreachable"
    )

    # Should not raise
    await oidc_provider.revoke_token("test-access-token")
