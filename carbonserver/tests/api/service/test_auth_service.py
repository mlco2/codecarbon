from unittest import mock

import pytest
from starlette.requests import Request

from carbonserver.api.routers import authenticate
from carbonserver.api.services import auth_service


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
    assert response.headers["location"] == "http://localhost:3000/home?auth=true"


def test_no_auth_login_rejects_external_redirect(monkeypatch):
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
            "query_string": b"redirect=https%3A%2F%2Fexample.com%2Fhome",
        }
    )

    assert authenticate.get_redirect_url(request) == "http://localhost:3000/home"
