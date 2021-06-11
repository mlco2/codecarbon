from uuid import UUID, uuid4
from contextlib import AbstractContextManager
from typing import List

from dependency_injector.providers import Callable

from carbonserver.api import schemas
from carbonserver.api.domain.teams import Teams
from carbonserver.api.schemas import Team, TeamCreate
from carbonserver.database.sql_models import Team as SqlModelTeam

"""
Here there is all the method to manipulate the team data
"""


class SqlAlchemyRepository(Teams):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def add_team(self, team: TeamCreate) -> Team:

        with self.session_factory() as session:
            db_team = SqlModelTeam(
                id=uuid4(),
                name=team.name,
                description=team.description,
                organization_id=team.organization_id
            )
            session.add(db_team)
            session.commit()
            session.refresh(db_team)
            return self.map_sql_to_schema(db_team)

    def get_one_team(self, team_id):
        """Find the team in database and return it

        :team_id: The id of the team to retreive.
        :returns: An Team in pyDantic BaseModel format.
        :rtype: schemas.Team
        """
        with self.session_factory() as session:
            e = session.query(SqlModelTeam).filter(SqlModelTeam.id == team_id).first()
            if e is None:
                return None
            else:
                return self.map_sql_to_schema(e)

    def list_teams(self):
        with self.session_factory() as session:
            e = session.query(SqlModelTeam)
            if e is None:
                return None
            else:
                teams: List[Team] = []
                for team in e:
                    teams.append(self.map_sql_to_schema(team))
                return teams

    def is_api_key_valid(self, organization_id: str, api_key: str):
        with self.session_factory() as session:
            e = (
                session.query(SqlModelTeam)
                    .filter(SqlModelTeam.id == organization_id)
                    .filter(SqlModelTeam.api_key == api_key)
                    .first()
            )
            if e is None:
                return False
            else:
                return True

    @staticmethod
    def map_sql_to_schema(team: SqlModelTeam) -> Team:
        return Team(
            id=team.id,
            name=team.name,
            description=team.description,
            organization_id=team.organization_id,
        )


class InMemoryRepository(Teams):
    def __init__(self):
        self.teams: List = []
        self.id: int = 0

    def add_team(self, team: TeamCreate, organization_id: UUID):
        self.teams.append(
            SqlModelTeam(
                id=self.id + 1,
                name=team.name,
                description=team.description,
                organization_id=team.organization_id,
            )
        )

    def get_one_team(self, team_id) -> Team:
        first_team = self.teams[0]
        return Team(
            id=first_team.id,
            name=first_team.name,
            description=first_team.description,
            organization_id=first_team.organization_id,
        )

    @staticmethod
    def get_db_to_class(team: SqlModelTeam) -> Team:
        return schemas.Team(
            id=team.id,
            name=team.name,
            description=team.description,
            organization_id=team.organization_id,
        )

    def list_team(self):
        teams = []
        for team in self.teams:
            teams.append(
                Team(
                    id=team.id,
                    name=team.name,
                    description=team.description,
                )
            )
        return teams
