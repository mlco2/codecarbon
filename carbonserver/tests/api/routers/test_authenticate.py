from unittest import mock

from api.mocks import FakeUserWithAuthDependency, MockAuthProvider
from dependency_injector import providers
from fastapi import FastAPI
from fastapi.testclient import TestClient

from carbonserver.api.routers import authenticate
from carbonserver.api.services.auth_service import OptionalUserWithAuthDependency
from carbonserver.container import ServerContainer


def make_app():
    container = ServerContainer()
    container.wire(modules=[authenticate])

    app = FastAPI()
    app.container = container
    app.include_router(authenticate.router)
    return app


def test_auth_check_logged_in():
    app = make_app()

    # Ensure dependency returns a fake logged user
    app.dependency_overrides[OptionalUserWithAuthDependency] = (
        FakeUserWithAuthDependency
    )

    sign_up_mock = mock.Mock()

    app.container.auth_provider.override(providers.Factory(MockAuthProvider))

    with app.container.sign_up_service.override(sign_up_mock):
        client = TestClient(app)
        response = client.get("/auth/check")

    assert response.status_code == 200
    assert response.json() == {"user": FakeUserWithAuthDependency.auth_user}
    sign_up_mock.check_jwt_user.assert_called_once_with(
        FakeUserWithAuthDependency.auth_user, create=True
    )


def test_auth_check_not_logged_in():
    app = make_app()

    class FakeNoUser:
        auth_user = None
        db_user = None

    app.dependency_overrides[OptionalUserWithAuthDependency] = FakeNoUser

    sign_up_mock = mock.Mock()

    app.container.auth_provider.override(providers.Factory(MockAuthProvider))

    with app.container.sign_up_service.override(sign_up_mock):
        client = TestClient(app)
        response = client.get("/auth/check")

    assert response.status_code == 200
    assert response.json() == {"user": None}
    sign_up_mock.check_jwt_user.assert_called_once_with(None, create=True)


def test_auth_callback_not_configured():
    app = make_app()

    # Force no auth provider configured
    app.container.auth_provider.override(lambda: None)

    client = TestClient(app)
    response = client.get("/auth/auth-callback?code=abc")

    assert response.status_code == 501


def test_login_not_configured():
    app = make_app()
    app.container.auth_provider.override(lambda: None)

    client = TestClient(app)
    response = client.get("/auth/login")

    assert response.status_code == 501


def test_login_redirects_to_authorize():
    app = make_app()

    # Provide the mock auth provider
    app.container.auth_provider.override(providers.Factory(MockAuthProvider))

    client = TestClient(app)
    response = client.get("/auth/login", allow_redirects=False)

    # Should be a redirect to the authorization endpoint
    assert response.status_code in (302, 307)
    location = response.headers.get("location", "")
    assert "https://auth.example/authorize" in location
    assert "client_id=clientid" in location
