from unittest import mock

from carbonserver.api.infra.repositories.repository_organizations import (
    SqlAlchemyRepository as OrgSqlRepository,
)
from carbonserver.api.infra.repositories.repository_teams import (
    SqlAlchemyRepository as TeamSqlRepository,
)
from carbonserver.api.infra.repositories.repository_users import (
    SqlAlchemyRepository as UserSqlRepository,
)
from carbonserver.api.schemas import Organization, Team, User, UserCreate
from carbonserver.api.services.signup_service import SignUpService

API_KEY = "9INn3JsdhCGzLAuOUC6rAw"
INVALID_API_KEY = "8INn3JsdhCGzLAuOUC6rAw"

ORG_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"

ORG_1 = Organization(
    id=ORG_ID,
    name="DFG",
    api_key=API_KEY,
    description="Data For Good Organization",
)


TEAM_ID = "f52fe339-164d-4c2b-a8c0-f562dfceteam"

TEAM_1 = Team(
    id=TEAM_ID,
    name="DFG Code Carbon",
    description="DFG Code Carbon Team",
    api_key=API_KEY,
    organization_id=ORG_ID,
)


USER_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"

USER_1 = User(
    id=USER_ID,
    name="Gontran Bonheur",
    email="xyz@email.com",
    password="pwd",
    api_key=API_KEY,
    is_active=True,
)


def test_sign_up_service_creates_full_new_user():
    expected_id = ORG_ID
    org_repository_mock: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)
    team_repository_mock: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    user_repository_mock: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    org_repository_mock.add_organization.return_value = ORG_1
    team_repository_mock.add_team.return_value = TEAM_1
    user_repository_mock.create_user.return_value = USER_1

    signup_service: SignUpService = SignUpService(
        user_repository_mock, org_repository_mock, team_repository_mock
    )

    user_to_create = UserCreate(
        name="Gontran Bonheur", email="xyz@email.com", password="pwd"
    )
    actual_saved_user = signup_service.sign_up(user_to_create)

    assert actual_saved_user.id == expected_id


def test_sign_up_service_creates_user_with_default():
    expected_id = ORG_ID
    org_repository_mock: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)
    team_mock_repository: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    user_repository_mock: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    org_repository_mock.add_organization.return_value = ORG_1
    team_mock_repository.add_team.return_value = TEAM_1
    user_repository_mock.create_user.return_value = USER_1

    signup_service: SignUpService = SignUpService(
        user_repository_mock, org_repository_mock, team_mock_repository
    )
    user_to_create = UserCreate(
        name="Gontran Bonheur", email="xyz@email.com", password="pwd"
    )
    actual_saved_user = signup_service.sign_up(user_to_create)

    assert actual_saved_user.id == expected_id


def test_add_user_to_org_adds_user_if_api_key_is_correct():

    user_mock_repository: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    team_mock_repository: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    org_mock_repository: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)

    user_service: SignUpService = SignUpService(
        user_mock_repository, org_mock_repository, team_mock_repository
    )

    joined_org = user_service.subscribe_user_to_org(USER_1, ORG_ID, API_KEY)

    org_mock_repository.is_api_key_valid.assert_called_with(ORG_ID, API_KEY)
    assert joined_org


def test_add_user_to_org_rejects_user_if_api_key_is_incorrect():

    user_mock_repository: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    team_mock_repository: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    org_mock_repository: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)
    org_mock_repository.is_api_key_valid.return_value = False

    user_service: SignUpService = SignUpService(
        user_mock_repository, org_mock_repository, team_mock_repository
    )

    joined_org = user_service.subscribe_user_to_org(USER_1, TEAM_ID, INVALID_API_KEY)

    org_mock_repository.is_api_key_valid.assert_called_with(TEAM_ID, INVALID_API_KEY)
    assert not joined_org


def test_add_user_to_team_adds_user_if_api_key_is_correct():

    user_mock_repository: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    team_mock_repository: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    org_mock_repository: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)

    user_service: SignUpService = SignUpService(
        user_mock_repository, org_mock_repository, team_mock_repository
    )

    joined_team = user_service.subscribe_user_to_team(USER_1, TEAM_ID, API_KEY)

    team_mock_repository.is_api_key_valid.assert_called_with(TEAM_ID, API_KEY)
    assert joined_team


def test_add_user_to_team_rejects_user_if_api_key_is_incorrect():

    user_mock_repository: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    team_mock_repository: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    org_mock_repository: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)
    team_mock_repository.is_api_key_valid.return_value = False

    user_service: SignUpService = SignUpService(
        user_mock_repository, org_mock_repository, team_mock_repository
    )

    joined_team = user_service.subscribe_user_to_team(USER_1, TEAM_ID, INVALID_API_KEY)

    team_mock_repository.is_api_key_valid.assert_called_with(TEAM_ID, INVALID_API_KEY)
    assert not joined_team
