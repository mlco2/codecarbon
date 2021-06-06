import uuid
from contextlib import AbstractContextManager
from typing import List

from dependency_injector.providers import Callable

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
                id=uuid.uuid4(),
                name=team.name,
                description=team.description,
            )
            session.add(db_team)
            session.commit()
            session.refresh(db_team)
            return self.get_db_to_class(db_team)

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
                return self.get_db_to_class(e)

    # def get_projects_from_team(self, team_id):
    # TODO : get Projects from Project id in database
    #    pass

    def list_team(self):
        # TODO : get Teams from Organization id in database
        pass

    @staticmethod
    def get_db_to_class(self, team: SqlModelTeam) -> Team:
        return schemas.Team(
            id=team.id,
            name=team.name,
            description=team.description,
            organization_id=team.organization_id,
        )


class InMemoryRepository(Teams):
    def __init__(self):
        self.teams: List = []
        self.id: int = 0

    def add_team(self, team: TeamCreate):
        self.teams.append(
            sql_models.Team(
                id=self.id + 1,
                name=team.name,
                description=team.description,
                # organization_id=team.organization_id,
            )
        )

    def get_one_team(self, team_id) -> Team:
        first_team = self.teams[0]
        return schemas.Team(
            id=first_team.id,
            name=first_team.name,
            description=first_team.description,
            # organization_id=first_team.organization_id,
        )

    # def get_projects_from_team(self, team_id):
    # TODO : get Projects from Project id in database
    #    pass

    @staticmethod
    def get_db_to_class(self, team: SqlModelTeam) -> Team:
        return schemas.Team(
            id=team.id,
            name=team.name,
            description=team.description,
            # organization_id=team.organization_id,
        )

    def list_team(self, team_name: str):
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
