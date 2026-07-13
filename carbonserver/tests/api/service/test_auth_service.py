import time
from unittest import mock

import jwt
import pytest
from starlette.requests import Request

from carbonserver.api.errors import AuthenticationError
from carbonserver.api.routers import authenticate
from carbonserver.api.services import auth_service

VICTIM_SUB = "d1b9d5e0-58e8-45f0-9ef5-4549b3d6f3f0"
DEV_JWT_KEY = "test-secret-key"


def _make_dependency():
    return auth_service.UserWithAuthDependency(error_if_not_found=True)


def _bearer(token: str):
    """Wrap a raw token like fastapi.security.HTTPBearer would."""
    return mock.Mock(credentials=token)


def _oidc_provider(claims=None, fail=False):
    """A mock OIDCAuthProvider whose JWKS validation returns claims or fails."""
    provider = mock.Mock()
    if fail:
        provider.get_user_info = mock.AsyncMock(side_effect=Exception("bad signature"))
    else:
        provider.get_user_info = mock.AsyncMock(return_value=claims)
    return provider


@pytest.mark.asyncio
async def test_no_auth_provider_uses_local_dev_user(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "auth_provider", "none")
    user_service = mock.Mock()
    sign_up_service = mock.Mock()

    dependency = auth_service.UserWithAuthDependency(error_if_not_found=True)
    result = await dependency(
        user_service=user_service,
        sign_up_service=sign_up_service,
        auth_provider=None,
    )

    assert result.auth_user == auth_service.LOCAL_DEV_AUTH_USER
    sign_up_service.check_jwt_user.assert_called_once_with(
        auth_service.LOCAL_DEV_AUTH_USER, create=True
    )
    user_service.get_user_by_id.assert_called_once_with(
        auth_service.LOCAL_DEV_AUTH_USER["sub"]
    )


@pytest.mark.asyncio
async def test_no_auth_login_redirects_to_frontend(monkeypatch):
    monkeypatch.setattr(authenticate.settings, "frontend_url", "http://localhost:3000")
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/auth/login",
            "headers": [],
            "scheme": "http",
            "server": ("localhost", 8008),
            "client": ("testclient", 50000),
            "query_string": b"redirect=http%3A%2F%2Flocalhost%3A3000%2Fhome%3Fauth%3Dtrue",
        }
    )

    response = await authenticate.get_login(request, auth_provider=None)

    assert response.status_code == 307
    assert response.headers["location"] == "http://localhost:3000/home"


# --- Cookie / bearer signature verification (OIDC mode) ---


@pytest.mark.asyncio
async def test_valid_cookie_is_verified_via_jwks(monkeypatch):
    """A signature-verified session cookie authenticates using the JWKS claims."""
    monkeypatch.setattr(auth_service.settings, "auth_provider", "oidc")
    claims = {"sub": VICTIM_SUB, "email": "victim@example.com"}
    provider = _oidc_provider(claims=claims)
    user_service = mock.Mock()

    result = await _make_dependency()(
        cookie_token="a.valid.token",
        bearer_token=None,
        user_service=user_service,
        sign_up_service=mock.Mock(),
        auth_provider=provider,
    )

    provider.get_user_info.assert_awaited_once_with("a.valid.token")
    assert result.auth_user == claims
    user_service.get_user_by_id.assert_called_once_with(VICTIM_SUB)


@pytest.mark.asyncio
async def test_forged_unsigned_cookie_is_rejected(monkeypatch):
    """The core issue: an unsigned/forged cookie must not authenticate anyone."""
    monkeypatch.setattr(auth_service.settings, "auth_provider", "oidc")
    monkeypatch.setattr(auth_service.settings, "environment", "production")
    # Attacker crafts {"sub": <victim>} — JWKS validation rejects it.
    forged = jwt.encode({"sub": VICTIM_SUB}, key="attacker-key", algorithm="HS256")
    user_service = mock.Mock()

    with pytest.raises(AuthenticationError) as exc_info:
        await _make_dependency()(
            cookie_token=forged,
            bearer_token=None,
            user_service=user_service,
            sign_up_service=mock.Mock(),
            auth_provider=_oidc_provider(fail=True),
        )

    assert exc_info.value.status_code == 401
    user_service.get_user_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_forged_unsigned_bearer_is_rejected(monkeypatch):
    """The bearer path is hardened the same way as the cookie path."""
    monkeypatch.setattr(auth_service.settings, "auth_provider", "oidc")
    monkeypatch.setattr(auth_service.settings, "environment", "production")
    forged = jwt.encode({"sub": VICTIM_SUB}, key="attacker-key", algorithm="HS256")

    with pytest.raises(AuthenticationError):
        await _make_dependency()(
            cookie_token=None,
            bearer_token=_bearer(forged),
            user_service=mock.Mock(),
            sign_up_service=mock.Mock(),
            auth_provider=_oidc_provider(fail=True),
        )


@pytest.mark.asyncio
async def test_missing_token_optional_dependency_returns_anonymous(monkeypatch):
    """No cookie and no bearer: optional auth yields an anonymous (None) user."""
    monkeypatch.setattr(auth_service.settings, "auth_provider", "oidc")
    dependency = auth_service.UserWithAuthDependency(error_if_not_found=False)

    result = await dependency(
        cookie_token=None,
        bearer_token=None,
        user_service=mock.Mock(),
        sign_up_service=mock.Mock(),
        auth_provider=_oidc_provider(fail=True),
    )

    assert result.auth_user is None
    assert result.db_user is None


# --- develop environment: local jwt_key tokens ---
#
# In `develop`, JWKS is still the primary verifier, but a token signed with the
# shared `settings.jwt_key` (HS256) is accepted as a fallback. This is what the
# black-box integration tests rely on (they mint `jwt.encode({"sub": ...},
# settings.jwt_key)`), since they have no live OIDC provider to sign tokens.


@pytest.mark.asyncio
async def test_develop_accepts_jwt_key_signed_cookie(monkeypatch):
    """develop: a jwt_key-signed cookie authenticates via the fallback path."""
    monkeypatch.setattr(auth_service.settings, "auth_provider", "oidc")
    monkeypatch.setattr(auth_service.settings, "environment", "develop")
    monkeypatch.setattr(auth_service.settings, "jwt_key", DEV_JWT_KEY)
    token = jwt.encode({"sub": VICTIM_SUB}, key=DEV_JWT_KEY, algorithm="HS256")
    user_service = mock.Mock()

    result = await _make_dependency()(
        cookie_token=token,
        bearer_token=None,
        user_service=user_service,
        sign_up_service=mock.Mock(),
        auth_provider=_oidc_provider(fail=True),  # not JWKS-signed
    )

    assert result.auth_user["sub"] == VICTIM_SUB
    user_service.get_user_by_id.assert_called_once_with(VICTIM_SUB)


@pytest.mark.asyncio
async def test_develop_accepts_jwt_key_signed_bearer(monkeypatch):
    """develop: the jwt_key fallback applies to the bearer path too."""
    monkeypatch.setattr(auth_service.settings, "auth_provider", "oidc")
    monkeypatch.setattr(auth_service.settings, "environment", "develop")
    monkeypatch.setattr(auth_service.settings, "jwt_key", DEV_JWT_KEY)
    token = jwt.encode({"sub": VICTIM_SUB}, key=DEV_JWT_KEY, algorithm="HS256")

    result = await _make_dependency()(
        cookie_token=None,
        bearer_token=_bearer(token),
        user_service=mock.Mock(),
        sign_up_service=mock.Mock(),
        auth_provider=None,  # jwt_key fallback works even without a provider
    )

    assert result.auth_user["sub"] == VICTIM_SUB


@pytest.mark.asyncio
async def test_develop_rejects_expired_jwt_key_token(monkeypatch):
    """develop: exp is enforced — an expired jwt_key token is rejected."""
    monkeypatch.setattr(auth_service.settings, "auth_provider", "oidc")
    monkeypatch.setattr(auth_service.settings, "environment", "develop")
    monkeypatch.setattr(auth_service.settings, "jwt_key", DEV_JWT_KEY)
    expired = jwt.encode(
        {"sub": VICTIM_SUB, "exp": int(time.time()) - 3600},
        key=DEV_JWT_KEY,
        algorithm="HS256",
    )

    with pytest.raises(AuthenticationError):
        await _make_dependency()(
            cookie_token=expired,
            bearer_token=None,
            user_service=mock.Mock(),
            sign_up_service=mock.Mock(),
            auth_provider=_oidc_provider(fail=True),
        )


@pytest.mark.asyncio
async def test_non_develop_rejects_jwt_key_token(monkeypatch):
    """Outside develop, the jwt_key fallback is disabled — only JWKS is trusted."""
    monkeypatch.setattr(auth_service.settings, "auth_provider", "oidc")
    monkeypatch.setattr(auth_service.settings, "environment", "production")
    monkeypatch.setattr(auth_service.settings, "jwt_key", DEV_JWT_KEY)
    token = jwt.encode({"sub": VICTIM_SUB}, key=DEV_JWT_KEY, algorithm="HS256")

    with pytest.raises(AuthenticationError):
        await _make_dependency()(
            cookie_token=token,
            bearer_token=None,
            user_service=mock.Mock(),
            sign_up_service=mock.Mock(),
            auth_provider=_oidc_provider(fail=True),
        )
