"""
Tests for issue #692 - missing/invalid tokens returning generic 500 error
instead of proper 401.
"""


class TestGetHttpException:
    """Tests for errors.py get_http_exception() - core fix for issue #692."""

    def test_user_error_api_key_unknown_returns_401(self):
        from carbonserver.carbonserver.api.errors import (
            UserError,
            UserErrorEnum,
            UserException,
            get_http_exception,
        )

        error = UserError(
            code=UserErrorEnum.API_KEY_UNKNOWN, message="API key not found"
        )
        result = get_http_exception(UserException(error))
        assert result.status_code == 401
        assert result.detail == "API key not found"

    def test_user_error_api_key_disabled_returns_401(self):
        from carbonserver.carbonserver.api.errors import (
            UserError,
            UserErrorEnum,
            UserException,
            get_http_exception,
        )

        error = UserError(
            code=UserErrorEnum.API_KEY_DISABLE, message="API key disabled"
        )
        result = get_http_exception(UserException(error))
        assert result.status_code == 401

    def test_generic_exception_returns_500_with_detail(self):
        from carbonserver.carbonserver.api.errors import get_http_exception

        result = get_http_exception(Exception("unexpected"))
        assert result.status_code == 500
        assert result.detail == "Internal Server Error"
