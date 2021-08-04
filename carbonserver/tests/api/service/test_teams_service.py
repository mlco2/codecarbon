from unittest import mock
from uuid import UUID

from carbonserver.api.infra.repositories.repository_teams import SqlAlchemyRepository
from carbonserver.api.schemas import Team, TeamCreate
from carbonserver.api.services.team_service import TeamService

API_KEY = "9INn3JsdhCGzLAuOUC6rAw"

ORG_ID = UUID("e52fe339-164d-4c2b-a8c0-f562dfce066d")
ORG_ID_2 = UUID("e395767d-0255-40f3-a314-5d2e01f56fbd")

TEAM_ID = UUID("c13e851f-5c2f-403d-98d0-51fe15df3bc3")
TEAM_ID_2 = UUID("dd011783-7d05-4376-ab60-9537738be25f")

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
    description="DFG Code Carbon 2",
    api_key=API_KEY,
    organization_id=ORG_ID_2,
)


@mock.patch("uuid.uuid4", return_value=TEAM_ID)
def test_teams_service_creates_correct_team(_):

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_id = TEAM_ID
    user_service: TeamService = TeamService(repository_mock)
    repository_mock.add_team.return_value = TEAM_1
    team_to_create = TeamCreate(
        name="DFG Code Carbon",
        description="DFG Code Carbon Team",
        organization_id=ORG_ID,
    )

    actual_saved_org = user_service.add_team(team_to_create)

    repository_mock.add_team.assert_called_with(team_to_create)
    assert actual_saved_org.id == expected_id


def test_teams_service_retrieves_all_existing_teams():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_team_ids_list = [TEAM_ID, TEAM_ID_2]
    organization_service: TeamService = TeamService(repository_mock)
    repository_mock.list_teams.return_value = [TEAM_1, TEAM_2]

    team_list = organization_service.list_teams()
    actual_team_ids_list = map(lambda x: x.id, iter(team_list))
    diff = set(actual_team_ids_list) ^ set(expected_team_ids_list)

    assert not diff
    assert len(team_list) == len(expected_team_ids_list)


def test_teams_service_retrieves_correct_team_by_id():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_org: Team = TEAM_1
    organization_service: TeamService = TeamService(repository_mock)
    repository_mock.get_one_team.return_value = TEAM_1

    actual_saved_org = organization_service.read_team(TEAM_ID)

    assert actual_saved_org.id == expected_org.id
    assert actual_saved_org.name == expected_org.name


def test_teams_service_retrieves_correct_team_by_organization_id():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_organization_id = ORG_ID
    team_service: TeamService = TeamService(repository_mock)
    repository_mock.get_teams_from_organization.return_value = [TEAM_1]

    actual_teams = team_service.list_teams_from_organization(ORG_ID)

    assert actual_teams[0].organization_id == expected_organization_id

