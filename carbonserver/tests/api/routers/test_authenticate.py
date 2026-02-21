from fastapi.testclient import TestClient

from carbonserver.main import app

SESSION_COOKIE_NAME = "user_session"

client = TestClient(app)


def test_logout_clears_cookie_and_session(monkeypatch):
    # Simulate a session and cookie
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

    # Set cookie in request
    cookies = {SESSION_COOKIE_NAME: "dummy_token"}
    response = client.get("/auth/logout", cookies=cookies)
    assert response.status_code == 200
    # Cookie should be deleted in response
    assert (
        SESSION_COOKIE_NAME not in response.cookies
        or response.cookies.get(SESSION_COOKIE_NAME) == ""
    )
    assert dummy_session.get("cleared")
    assert "window.location.href" in response.text
