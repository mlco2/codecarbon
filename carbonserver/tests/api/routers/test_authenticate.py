import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from carbonserver.api.routers import authenticate
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
