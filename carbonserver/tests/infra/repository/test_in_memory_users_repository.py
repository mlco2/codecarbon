import unittest

import pytest
from unittest.mock import patch

from carbonserver.api.infra.repositories.repository_users import (
    InMemoryRepository,
    hash_password,
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
            "password": "john",
            "api_key": "key",
            "is_active": True,
        }
    )
    return model_user


def test_user_repository_saves_correct_user(user_repository):
    user = UserCreate.parse_obj(
        {
            "name": "John McLane",
            "email": "mclane@grubber.io",
            "password": "john",
            "api_key": "key",
            "is_active": True,
        }
    )

    created_user = user_repository.create_user(user)

    assert created_user.user_id == 1
    assert type(created_user.hashed_password) == bytes


class TestPasswordHasing(unittest.TestCase):
    @patch("carbonserver.api.infra.repositories.repository_users.random_generator")
    def test_hash_password_returns_salt_and_hashed_password(
        self, mock_random_generator
    ):
        password = "john"
        expected_salt = b"\xf1\x0f\xd2\xbeL\x81\x0f\xdf\x84\xc1\xea\xedm\xe8\xb1Iy\xbbT<h\x05=>\x0b\n\xa5\xc3\xfd\x93\xa3m"
        expected_key = b"\x8f\x18z\xed\x1c\xcc\xa0\x17\x00\x13\x01\x05\xa9\tu\xb8dw\x16\x92\xc8l\x9eF\xb5H\x13~E~\x8b9"
        mock_random_generator._mock_return_value = expected_salt
        actual_password = hash_password(password)
        actual_salt = actual_password[:32]
        actual_key = actual_password[32:]

        assert expected_salt == actual_salt
        assert expected_key == actual_key
