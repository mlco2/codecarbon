from unittest import mock

from pydantic.types import SecretStr

from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository
from carbonserver.api.schemas import User, UserCreate
from carbonserver.api.services.user_service import UserService

USER_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"
USER_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce066d"

USER_1 = User(
    id=USER_ID,
    name="Gontran Bonheur",
    email="xyz@email.com",
    password="pwd",
    api_key="AZEZAEAZEAZE",
    is_active=True,
)

USER_2 = User(
    id=USER_ID_2,
    name="Jonnhy Monnay",
    email="1234+1@email.fr",
    password="password",
    api_key="BZEZBEBZEBZE",
    is_active=True,
)


@mock.patch("uuid.uuid4", return_value=USER_ID)
def test_user_service_creates_correct_user_on_sign_up(_):

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_id = USER_ID
    user_service: UserService = UserService(repository_mock)
    repository_mock.create_user.return_value = USER_1
    user_to_create: UserCreate = UserCreate(
        name="Gontran Bonheur", email="xyz@email.com", password="pwd"
    )

    actual_db_user = user_service.create_user(user_to_create)

    repository_mock.create_user.assert_called_with(user_to_create)
    assert actual_db_user.id == expected_id


def test_user_service_retrieves_all_existing_users():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_user_ids_list = [USER_ID, USER_ID_2]
    user_service: UserService = UserService(repository_mock)
    repository_mock.list_users.return_value = [USER_1, USER_2]

    actual_user_list = user_service.list_users()
    actual_user_ids_list = map(lambda x: x.id, iter(actual_user_list))
    diff = set(actual_user_ids_list) ^ set(expected_user_ids_list)

    assert not diff
    assert len(actual_user_list) == len(expected_user_ids_list)


def test_user_service_retrieves_correct_user_by_id():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_user: User = USER_1
    user_service: UserService = UserService(repository_mock)
    repository_mock.get_user_by_id.return_value = USER_1

    actual_saved_user = user_service.get_user_by_id(USER_ID)

    assert actual_saved_user.id == expected_user.id
    assert actual_saved_user.name == expected_user.name
