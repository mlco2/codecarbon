import importlib.util
from pathlib import Path
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from carbonserver.api.errors import (
    NotAllowedError,
    NotAllowedErrorEnum,
    NotFoundError,
    NotFoundErrorEnum,
    UserException,
)

MAIN_PATH = Path(__file__).parents[3] / "main.py"


def load_main():
    """Import carbonserver/main.py without touching a database."""
    spec = importlib.util.spec_from_file_location("carbonserver_main", MAIN_PATH)
    module = importlib.util.module_from_spec(spec)
    with mock.patch("sqlalchemy.MetaData.create_all"):
        spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def main_module():
    return load_main()


@pytest.mark.parametrize(
    "error, status_code",
    [
        (
            NotAllowedError(
                code=NotAllowedErrorEnum.NOT_IN_ORGANISATION, message="Not allowed"
            ),
            403,
        ),
        (NotFoundError(code=NotFoundErrorEnum.NOT_FOUND, message="Not found"), 404),
    ],
)
def test_user_exception_returns_its_http_status(main_module, error, status_code):
    app = main_module.app

    async def raise_user_exception():
        raise UserException(error)

    path = f"/raise-user-exception-{status_code}"
    app.add_api_route(path, raise_user_exception)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get(path)

    assert response.status_code == status_code
    assert response.json() == {"detail": error.message}
