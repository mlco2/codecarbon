"""
End-to-end auth flow against a running API using Fief + fastapi-oidc.

Required environment variables (test is skipped if any is missing):
    CODECARBON_API_URL        Base API URL (e.g. https://api.dev/codecarbon/api)
    FIEF_TEST_USER_EMAIL      Login email for the test user
    FIEF_TEST_USER_PASSWORD   Login password for the test user
    CODECARBON_TEST_ORG_ID    Organization ID in which to create the project/experiment

To run this:
    export $(cat ./carbonserver/tests/api/integration/.env | xargs) && uv run pytest carbonserver/tests/api/integration/test_auth_fief_cookie_flow.py -vv
"""

import os
import uuid
from html.parser import HTMLParser
from urllib.parse import urljoin

import pytest
import requests

SESSION_COOKIE_NAME = "user_session"


class _FormParser(HTMLParser):
    """Small HTML form parser to collect the first form action + inputs."""

    def __init__(self):
        super().__init__()
        self.form_action = None
        self.inputs = {}
        self._inside_form = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag.lower() == "form" and self.form_action is None:
            self._inside_form = True
            self.form_action = attrs_dict.get("action")
        if tag.lower() == "input" and self._inside_form:
            name = attrs_dict.get("name")
            if name:
                self.inputs[name] = attrs_dict.get("value", "")

    def handle_endtag(self, tag):
        if tag.lower() == "form":
            self._inside_form = False


def _parse_login_form(response: requests.Response):
    parser = _FormParser()
    parser.feed(response.text)
    if parser.form_action is None:
        raise AssertionError("Could not find login form action on the Fief page.")
    return parser.form_action, parser.inputs


def _assert_env(var: str) -> str:
    val = os.getenv(var)
    if not val:
        pytest.skip(f"Missing required env var: {var}")
    return val


def _api_base_url() -> str:
    url = _assert_env("CODECARBON_API_URL").rstrip("/")
    return url if url.endswith("/api") else url + "/api"


def _login_via_fief(session: requests.Session) -> str:
    """
    Perform the auth code flow against /auth/login, follow the Fief login page,
    and return the access token set in the session cookie.
    """
    api_url = _api_base_url()
    login_url = f"{api_url}/auth/login"
    resp = session.get(login_url, allow_redirects=True, timeout=15)
    assert (
        resp.status_code == 200
    ), f"Unexpected status fetching login page: {resp.status_code}"

    action, inputs = _parse_login_form(resp)
    inputs["email"] = _assert_env("FIEF_TEST_USER_EMAIL")
    inputs["password"] = _assert_env("FIEF_TEST_USER_PASSWORD")

    action_url = urljoin(resp.url, action)
    resp = session.post(action_url, data=inputs, allow_redirects=True, timeout=15)
    assert resp.status_code in (200, 302, 303), f"Login POST failed: {resp.status_code}"
    assert (
        SESSION_COOKIE_NAME in session.cookies
    ), "Expected auth cookie to be set after login."
    return session.cookies[SESSION_COOKIE_NAME]


def test_fief_cookie_and_bearer_flow():
    api_url = _api_base_url()
    org_id = _assert_env("CODECARBON_TEST_ORG_ID")

    session = requests.Session()
    session.headers["Accept"] = "application/json"

    access_token = _login_via_fief(session)

    # Cookie flow
    cookie_resp = session.get(f"{api_url}/auth/check", timeout=10)
    assert (
        cookie_resp.status_code == 200
    ), f"Cookie auth failed: {cookie_resp.status_code}"
    cookie_user = cookie_resp.json().get("user")
    assert cookie_user and cookie_user.get("sub"), "Cookie auth did not return a user."

    # Bearer flow using the cookie's access token
    bearer_session = requests.Session()
    bearer_session.headers.update(
        {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    )
    bearer_resp = bearer_session.get(f"{api_url}/auth/check", timeout=10)
    assert (
        bearer_resp.status_code == 200
    ), f"Bearer auth failed: {bearer_resp.status_code}"

    project_payload = {
        "name": f"auth-flow-{uuid.uuid4()}",
        "description": "Created by test_fief_cookie_and_bearer_flow",
        "organization_id": org_id,
    }
    project_resp = session.post(
        f"{api_url}/projects/", json=project_payload, timeout=10
    )
    assert (
        project_resp.status_code == 201
    ), f"Project creation failed: {project_resp.status_code} {project_resp.text}"
    project_id = project_resp.json()["id"]

    # Create an experiment in the project
    experiment_payload = {
        "name": f"auth-flow-{uuid.uuid4()}",
        "description": "Created by test_fief_cookie_and_bearer_flow",
        "timestamp": "2025-01-01T00:00:00Z",
        "country_name": "France",
        "country_iso_code": "FRA",
        "region": "france",
        "on_cloud": True,
        "cloud_provider": "devcloud",
        "cloud_region": "eu-west-1a",
        "project_id": project_id,
    }
    experiment_resp = session.post(
        f"{api_url}/experiments", json=experiment_payload, timeout=10
    )
    assert (
        experiment_resp.status_code == 201
    ), f"Experiment creation failed: {experiment_resp.status_code} {experiment_resp.text}"

    # Cleanup: delete the created project (which also deletes the experiment)
    delete_resp = session.delete(f"{api_url}/projects/{project_id}", timeout=10)
    assert (
        delete_resp.status_code == 204
    ), f"Project deletion failed: {delete_resp.status_code} {delete_resp.text}"
