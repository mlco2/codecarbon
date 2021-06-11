from unittest import mock

from carbonserver.api.infra.repositories.repository_organizations import SqlAlchemyRepository as OrgSqlRepository
from carbonserver.api.infra.repositories.repository_teams import SqlAlchemyRepository as TeamSqlRepository
from carbonserver.api.infra.repositories.repository_users import SqlAlchemyRepository as UserSqlRepository
from carbonserver.api.schemas import Organization, Team, User, OrganizationCreate, TeamCreate, UserCreate
from carbonserver.api.services.signup_service import SignUpService

ORG_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"

ORG_1 = Organization(
    id=ORG_ID,
    name="DFG",
    description="Data For Good Organization",
    api_key="a"
)

API_KEY = "9INn3JsdhCGzLAuOUC6rAw"
INVALID_API_KEY = "8INn3JsdhCGzLAuOUC6rAw"

TEAM_ID = "f52fe339-164d-4c2b-a8c0-f562dfceteam"

TEAM_1 = Team(
    id=TEAM_ID,
    name="DFG Code Carbon",
    description="DFG Code Carbon Team",
    organization_id=ORG_ID,
)


USER_ID = "f52fe339-164d-4c2b-a8c0-f562dfce066d"

USER_1 = User(
    id=USER_ID,
    name="Gontran Bonheur",
    email="xyz@email.com",
    password="pwd",
    api_key="AZEZAEAZEAZE",
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

    signup_service: SignUpService = SignUpService(user_repository_mock,
                                                  org_repository_mock,
                                                  team_repository_mock)
    org_to_create = OrganizationCreate(
        name="Data For Good",
        description="Data For Good Organization"
    )

    team_to_create = TeamCreate(
        name="DFG Code Carbon",
        description="DFG Code Carbon Team",
        organization_id=ORG_ID,
    )

    user_to_create = UserCreate(
        name="Gontran Bonheur",
        email="xyz@email.com",
        password="pwd"
    )
    actual_saved_user = signup_service.sign_up(user_to_create,
                                               org_to_create,
                                               team_to_create)

    assert actual_saved_user.id == expected_id


def test_sign_up_service_creates_user_with_default():
    expected_id = ORG_ID
    org_repository_mock: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)
    team_repository_mock: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    user_repository_mock: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    org_repository_mock.add_organization.return_value = ORG_1
    team_repository_mock.add_team.return_value = TEAM_1
    user_repository_mock.create_user.return_value = USER_1

    signup_service: SignUpService = SignUpService(user_repository_mock,
                                                  org_repository_mock,
                                                  team_repository_mock)
    org_to_create = OrganizationCreate(
        name="Data For Good",
        description="Data For Good Organization"
    )

    team_to_create = TeamCreate(
        name="DFG Code Carbon",
        description="DFG Code Carbon Team",
        organization_id=ORG_ID,
    )

    user_to_create = UserCreate(
        name="Gontran Bonheur",
        email="xyz@email.com",
        password="pwd"
    )
    actual_saved_user = signup_service.sign_up(user_to_create,
                                               org_to_create,
                                               team_to_create)

    assert actual_saved_user.id == expected_id


def test_add_user_to_org_adds_user_if_api_key_is_correct():

    user_mock_repository: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    team_repository_mock: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    org_mock_repository: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)

    user_service: SignUpService = SignUpService(user_mock_repository, org_mock_repository, team_repository_mock)

    joined = user_service.add_user_to_org(USER_1, ORG_ID, API_KEY)

    org_mock_repository.is_api_key_valid.assert_called_with(ORG_ID, API_KEY)
    assert joined


def test_add_user_to_org_rejects_user_if_api_key_is_incorrect():

    user_mock_repository: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    team_repository_mock: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    org_mock_repository: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)
    org_mock_repository.is_api_key_valid.return_value = False

    user_service: SignUpService = SignUpService(user_mock_repository, org_mock_repository, team_repository_mock)

    joined = user_service.add_user_to_org(USER_1, ORG_ID, INVALID_API_KEY)

    org_mock_repository.is_api_key_valid.assert_called_with(ORG_ID, INVALID_API_KEY)
    assert not joined
