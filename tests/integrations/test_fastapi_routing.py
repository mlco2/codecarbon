"""Tests for route naming and endpoint filter helpers."""

from unittest.mock import MagicMock

from codecarbon.integrations.fastapi._routing import (
    build_endpoint_key,
    build_task_name,
    matches_exclude,
    should_track_request,
)


def test_build_task_name_uses_route_template() -> None:
    request = MagicMock()
    request.method = "GET"
    route = MagicMock()
    route.path = "/users/{user_id}"
    request.scope = {"route": route}
    assert build_task_name(request) == "GET /users/{user_id}"


def test_build_task_name_custom_formatter() -> None:
    request = MagicMock()
    request.url.path = "/webhook"
    assert (
        build_task_name(request, formatter=lambda r: f"custom:{r.url.path}")
        == "custom:/webhook"
    )


def test_build_task_name_fallback_to_url_path() -> None:
    request = MagicMock()
    request.method = "POST"
    request.scope = {}
    request.url.path = "/webhook"
    assert build_task_name(request) == "POST /webhook"


def _mock_request(method: str, route_path: str | None, url_path: str) -> MagicMock:
    request = MagicMock()
    request.method = method
    request.url.path = url_path
    if route_path is None:
        request.scope = {}
    else:
        route = MagicMock()
        route.path = route_path
        request.scope = {"route": route}
    return request


def test_build_endpoint_key_uses_route_template() -> None:
    request = _mock_request("GET", "/predict", "/predict")
    assert build_endpoint_key(request) == "GET /predict"


def test_matches_exclude_path_prefix() -> None:
    assert (
        matches_exclude("/docs", "/docs/oauth2-redirect", "GET /docs", "/docs") is True
    )
    assert matches_exclude("/health", "/health", "GET /health", "/health") is True


def test_should_track_request_exclude_by_method_and_path() -> None:
    request = _mock_request("GET", "/predict", "/predict")
    assert should_track_request(request, None, ["GET /predict"]) is False
    assert should_track_request(request, None, ["POST /predict"]) is True


def test_should_track_request_exclude_path_only() -> None:
    request = _mock_request("POST", "/predict", "/predict")
    assert should_track_request(request, None, ["/predict"]) is False


def test_should_track_request_include_allowlist() -> None:
    request = _mock_request("GET", "/predict", "/predict")
    other = _mock_request("GET", "/health", "/health")
    include = ["GET /predict"]
    assert should_track_request(request, include, []) is True
    assert should_track_request(other, include, []) is False


def test_should_track_request_include_path_only() -> None:
    get_request = _mock_request("GET", "/predict", "/predict")
    post_request = _mock_request("POST", "/predict", "/predict")
    include = ["/predict"]
    assert should_track_request(get_request, include, []) is True
    assert should_track_request(post_request, include, []) is True
