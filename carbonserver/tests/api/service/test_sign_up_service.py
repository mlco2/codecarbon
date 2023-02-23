from unittest import mock
from uuid import UUID

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

ORG_ID = UUID("e52fe339-164d-4c2b-a8c0-f562dfce066d")
ORG_ID_2 = UUID("f688133d-2cb9-41f0-9362-a4c05ceb0dd8")

ORG_1 = Organization(
    id=ORG_ID,
    name="DFG",
    api_key=API_KEY,
    description="Data For Good Organization",
)

ORG_2 = Organization(
    id=ORG_ID_2,
    name="ORG2",
    api_key=API_KEY,
    description="Data For Good Organization 2",
)


TEAM_ID = UUID("8edb03e1-9a28-452a-9c93-a3b6560136d7")
TEAM_ID_2 = UUID("8edb03e1-9a28-452a-9c93-a3b6560136d6")

TEAM_1 = Team(
    id=TEAM_ID,
    name="DFG Code Carbon",
    description="DFG Code Carbon Team",
    api_key=API_KEY,
    organization_id=ORG_ID,
)

TEAM_2 = Team(
    id=TEAM_ID_2,
    name="DFG Code Carbon 2",
    description="DFG Code Carbon Team 2",
    api_key=API_KEY,
    organization_id=ORG_ID,
)


USER_ID = UUID("f52fe339-164d-4c2b-a8c0-f562dfce066d")

USER_1 = User(
    id=USER_ID,
    name="Gontran Bonheur",
    email="xyz@email.com",
    api_key=API_KEY,
    teams=[],
    organizations=[],
    is_active=True,
)

USER_IN_DEFAULT_ORG = User(
    id=USER_ID,
    name="Gontran Bonheur",
    email="xyz@email.com",
    api_key=API_KEY,
    teams=[],
    organizations=[ORG_ID],
    is_active=True,
)

USER_IN_DEFAULT_ORG_AND_TEAM = User(
    id=USER_ID,
    name="Gontran Bonheur",
    email="xyz@email.com",
    api_key=API_KEY,
    teams=[TEAM_ID],
    organizations=[ORG_ID],
    is_active=True,
)


def test_sign_up_service_creates_user_with_default_team_and_organisation():
    org_repository_mock: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)
    team_mock_repository: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    user_repository_mock: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    org_repository_mock.add_organization.return_value = ORG_1
    team_mock_repository.add_team.return_value = TEAM_1
    user_repository_mock.create_user.return_value = USER_1
    user_repository_mock.subscribe_user_to_org.return_value = USER_IN_DEFAULT_ORG
    user_repository_mock.subscribe_user_to_team.return_value = (
        USER_IN_DEFAULT_ORG_AND_TEAM
    )

    signup_service: SignUpService = SignUpService(
        user_repository_mock, org_repository_mock, team_mock_repository
    )
    user_to_create = UserCreate(
        name="Gontran Bonheur", email="xyz@email.com", password="pwd"
    )
    signup_service.sign_up(user_to_create)

    user_repository_mock.subscribe_user_to_org.assert_called_with(USER_1, ORG_ID)
    user_repository_mock.subscribe_user_to_team.assert_called_with(USER_1, TEAM_ID)


def test_add_user_to_org_adds_user_if_api_key_is_correct():
    user_mock_repository: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    team_mock_repository: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    org_mock_repository: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)

    signup_service: SignUpService = SignUpService(
        user_mock_repository, org_mock_repository, team_mock_repository
    )

    signup_service.subscribe_user_to_org(USER_1, ORG_ID_2, API_KEY)

    org_mock_repository.is_api_key_valid.assert_called_with(ORG_ID_2, API_KEY)
    user_mock_repository.subscribe_user_to_org.assert_called_with(USER_1, ORG_ID_2)


def test_add_user_to_org_rejects_user_if_api_key_is_incorrect():
    user_mock_repository: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    team_mock_repository: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    org_mock_repository: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)
    org_mock_repository.is_api_key_valid.return_value = False
    user_mock_repository.subscribe_user_to_org.return_value = USER_IN_DEFAULT_ORG
    user_mock_repository.subscribe_user_to_team.return_value = (
        USER_IN_DEFAULT_ORG_AND_TEAM
    )

    signup_service: SignUpService = SignUpService(
        user_mock_repository, org_mock_repository, team_mock_repository
    )

    signup_service.subscribe_user_to_org(USER_1, ORG_ID_2, INVALID_API_KEY)
    org_mock_repository.is_api_key_valid.assert_called_with(ORG_ID_2, INVALID_API_KEY)
    assert not user_mock_repository.subscribe_user_to_org.called


def test_add_user_to_team_adds_user_if_api_key_is_correct():
    user_mock_repository: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    team_mock_repository: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    org_mock_repository: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)

    signup_service: SignUpService = SignUpService(
        user_mock_repository, org_mock_repository, team_mock_repository
    )

    signup_service.subscribe_user_to_team(USER_1, TEAM_ID_2, API_KEY)

    user_mock_repository.subscribe_user_to_team.assert_called_with(USER_1, TEAM_ID_2)


def test_add_user_to_team_rejects_user_if_api_key_is_incorrect():
    user_mock_repository: UserSqlRepository = mock.Mock(spec=UserSqlRepository)
    team_mock_repository: TeamSqlRepository = mock.Mock(spec=TeamSqlRepository)
    org_mock_repository: OrgSqlRepository = mock.Mock(spec=OrgSqlRepository)
    team_mock_repository.is_api_key_valid.return_value = False

    signup_service: SignUpService = SignUpService(
        user_mock_repository, org_mock_repository, team_mock_repository
    )

    signup_service.subscribe_user_to_team(USER_1, TEAM_ID_2, INVALID_API_KEY)

    team_mock_repository.is_api_key_valid.assert_called_with(TEAM_ID_2, INVALID_API_KEY)
    assert not user_mock_repository.subscribe_user_to_team.called
