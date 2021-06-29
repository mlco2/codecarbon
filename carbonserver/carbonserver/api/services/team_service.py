from carbonserver.api.infra.repositories.repository_teams import SqlAlchemyRepository
from carbonserver.api.schemas import Team, TeamCreate


class TeamService:
    def __init__(self, team_repository: SqlAlchemyRepository):
        self._repository = team_repository

    def add_team(self, team: TeamCreate) -> Team:

        created_team = self._repository.add_team(team)
        return created_team

    def read_team(self, team_id: str) -> Team:
        return self._repository.get_one_team(team_id)

    def list_teams(self):
        return self._repository.list_teams()
