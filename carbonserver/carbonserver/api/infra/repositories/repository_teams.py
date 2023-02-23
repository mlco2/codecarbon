from contextlib import AbstractContextManager
from typing import List
from uuid import UUID, uuid4

from dependency_injector.providers import Callable
from fastapi import HTTPException

from carbonserver.api.domain.teams import Teams
from carbonserver.api.infra.api_key_service import generate_api_key
from carbonserver.api.infra.database.sql_models import Team as SqlModelTeam
from carbonserver.api.schemas import Team, TeamCreate

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
                api_key=generate_api_key(),
                organization_id=team.organization_id,
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
                raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
            return self.map_sql_to_schema(e)

    def list_teams(self):
        with self.session_factory() as session:
            e = session.query(SqlModelTeam)
            if e is None:
                return None
            teams: List[Team] = []
            for team in e:
                teams.append(self.map_sql_to_schema(team))
            return teams

    def get_teams_from_organization(self, organization_id) -> List[Team]:
        """Find the list of teams from an organization in database and return it

        :organization_id: The id of the organization to retreive teams from.
        :returns: List of Teams in pyDantic BaseModel format.
        :rtype: List[schemas.Team]
        """
        with self.session_factory() as session:
            res = session.query(SqlModelTeam).filter(
                SqlModelTeam.organization_id == organization_id
            )
            if res.first() is None:
                return []
            return [self.map_sql_to_schema(e) for e in res]

    def is_api_key_valid(self, organization_id: UUID, api_key: str):
        with self.session_factory() as session:
            return bool(
                session.query(SqlModelTeam)
                .filter(SqlModelTeam.id == organization_id)
                .filter(SqlModelTeam.api_key == api_key)
                .first()
            )

    @staticmethod
    def map_sql_to_schema(team: SqlModelTeam) -> Team:
        return Team(
            id=str(team.id),
            name=team.name,
            api_key=team.api_key,
            description=team.description,
            organization_id=str(team.organization_id),
        )
