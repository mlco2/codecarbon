"""Tests for route naming and endpoint filter helpers."""

from unittest.mock import MagicMock

from codecarbon.integrations.fastapi._routing import build_endpoint_key, should_track_request


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


def test_should_track_request_exclude_path_prefix() -> None:
    request = _mock_request("GET", "/docs", "/docs/oauth2-redirect")
    assert should_track_request(request, None, ["/docs"]) is False


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
