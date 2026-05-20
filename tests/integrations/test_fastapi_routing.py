"""Tests for route naming and path exclusion helpers."""

from unittest.mock import MagicMock

from codecarbon.integrations.fastapi._routing import (
    build_task_name,
    should_skip_path,
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
    assert build_task_name(request, formatter=lambda r: f"custom:{r.url.path}") == "custom:/webhook"


def test_build_task_name_fallback_to_url_path() -> None:
    request = MagicMock()
    request.method = "POST"
    request.scope = {}
    request.url.path = "/webhook"
    assert build_task_name(request) == "POST /webhook"


def test_should_skip_path_matches_prefixes() -> None:
    assert should_skip_path("/health", {"/health", "/docs"})
    assert should_skip_path("/docs/oauth2-redirect", {"/docs"})
    assert not should_skip_path("/api/v1/runs", {"/health", "/docs"})
