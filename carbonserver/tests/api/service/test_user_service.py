from unittest import mock

from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.api.schemas import UserCreate
from carbonserver.api.services.user_service import UserService
from carbonserver.database.sql_models import User as ModelUser


@mock.patch("uuid.uuid4", return_value="f52fe339-164d-4c2b-a8c0-f562dfce066d")
def test_user_service_creates_correct_user_on_sign_up(_):
    # Given
    repository_mock = mock.Mock(spec=SqlAlchemyRepository)
    expected_id = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
    user_service = UserService(repository_mock)
    repository_mock.create_user.return_value = ModelUser(
        user_id="f52fe339-164d-4c2b-a8c0-f562dfce066d",
        name="Gontran Bonheur",
        email="xyz@email.com",
        hashed_password="pwd",
        is_active=True,
    )
    user_to_create = UserCreate(
        name="Gontran Bonheur", email="xyz@email.com", password="pwd"
    )

    # When
    actual_db_user = user_service.create_user(user_to_create)

    # Then
    repository_mock.create_user.assert_called_with(user_to_create)
    assert actual_db_user.user_id == expected_id
