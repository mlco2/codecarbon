import pytest

from carbonserver.api.infra.repositories.repository_users import (
    InMemoryRepository
)
from carbonserver.api.schemas import UserCreate
from carbonserver.database.models import User as ModelUser


@pytest.fixture()
def user_repository():
    repo = InMemoryRepository()
    return repo


@pytest.fixture()
def user_fixture() -> UserCreate:
    user = UserCreate.parse_obj(
        {
            "user_id": 1,
            "name": "John McLane",
            "email": "mclane@grubber.io",
            "password": "john",
            "api_key": "key",
            "is_active": True,
        }
    )
    return user


@pytest.fixture()
def model_user() -> ModelUser:
    model_user = ModelUser(
        **{
            "name": "John McLane",
            "email": "mclane@grubber.io",
            "hashed_password": "john",
            "api_key": "key"
        }
    )
    return model_user


def test_create_user_saves_correct_user(user_repository):
    user = UserCreate.parse_obj(
        {
            "name": "John McLane",
            "email": "mclane@grubber.io",
            "password": "john"
        }
    )

    created_user = user_repository.create_user(user)

    assert created_user.user_id == 1


def test_list_users_returns_all_users(user_repository):
    user1 = UserCreate.parse_obj(
        {
            "name": "John McLane",
            "email": "mclane@grubber.io",
            "password": "john"
        }
    )

    user2 = UserCreate.parse_obj(
        {
            "name": "Simon Gruber",
            "email": "Simon@grubber.io",
            "password": "john"
        }
    )

    user_repository.create_user(user1)
    user_repository.create_user(user2)
    expected_user_ids = [1, 2]

    actual_users = user_repository.list_users()
    actual_user_ids = [user.user_id for user in actual_users]
    assert expected_user_ids == actual_user_ids


def test_get_user_by_id_returns_correct_user(user_repository):
    user1 = UserCreate.parse_obj(
        {
            "name": "John McLane",
            "email": "mclane@grubber.io",
            "password": "john"
        }
    )

    user2 = UserCreate.parse_obj(
        {
            "name": "Simon Gruber",
            "email": "Simon@grubber.io",
            "password": "john"
        }
    )

    user_repository.create_user(user1)
    user_repository.create_user(user2)
    expected_user_email = "Simon@grubber.io"
    expected_user_id = 2

    actual_user = user_repository.get_user_by_id(expected_user_id)

    assert expected_user_email == actual_user.email
