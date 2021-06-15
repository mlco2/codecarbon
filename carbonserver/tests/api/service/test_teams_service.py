from unittest import mock

from carbonserver.api.infra.repositories.repository_teams import SqlAlchemyRepository
from carbonserver.api.schemas import Team, TeamCreate
from carbonserver.api.services.team_service import TeamService

ORG_ID = "f52fe339-164d-4c2b-a8c0-f562dfce0org"
ORG_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfce0org"

TEAM_ID = "f52fe339-164d-4c2b-a8c0-f562dfceteam"
TEAM_ID_2 = "e52fe339-164d-4c2b-a8c0-f562dfceteam"

TEAM_1 = Team(
    id=TEAM_ID,
    name="DFG Code Carbon",
    description="DFG Code Carbon Team",
    organization_id=ORG_ID,
)

ORG_2 = Team(
    id=TEAM_ID_2,
    name="DFG Code Carbon 2",
    description="DFG Code Carbon 2",
    organization_id=ORG_ID_2,
)


@mock.patch("uuid.uuid4", return_value=TEAM_ID)
def test_organization_service_creates_correct_user_on_sign_up(_):

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_id = TEAM_ID
    user_service: TeamService = TeamService(repository_mock)
    repository_mock.add_team.return_value = TEAM_1
    org_to_create = TeamCreate(
        name="DFG Code Carbon",
        description="DFG Code Carbon Team",
        organization_id=ORG_ID,
    )

    actual_saved_org = user_service.add_team(org_to_create)

    repository_mock.add_team.assert_called_with(org_to_create)
    assert actual_saved_org.id == expected_id


def test_organiation_service_retrieves_all_existing_organizations():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_team_ids_list = [TEAM_ID, TEAM_ID_2]
    organization_service: TeamService = TeamService(repository_mock)
    repository_mock.list_teams.return_value = [TEAM_1, ORG_2]

    team_list = organization_service.list_team()
    actual_team_ids_list = map(lambda x: x.id, iter(team_list))
    diff = set(actual_team_ids_list) ^ set(expected_team_ids_list)

    assert not diff
    assert len(team_list) == len(expected_team_ids_list)


def test_organization_service_retrieves_correct_org_by_id():

    repository_mock: SqlAlchemyRepository = mock.Mock(spec=SqlAlchemyRepository)
    expected_org: Team = TEAM_1
    organization_service: TeamService = TeamService(repository_mock)
    repository_mock.get_one_team.return_value = TEAM_1

    actual_saved_org = organization_service.read_team(TEAM_ID)

    assert actual_saved_org.id == expected_org.id
    assert actual_saved_org.name == expected_org.name
