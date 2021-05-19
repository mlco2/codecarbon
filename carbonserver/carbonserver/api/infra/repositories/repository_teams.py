from typing import List
from carbonserver.api.domain.teams import Teams
from carbonserver.database import models
from carbonserver.api import schemas
from sqlalchemy.orm import Session

"""
Here there is all the method to manipulate the project data
"""


class SqlAlchemyRepository(Teams):
    def __init__(self, db: Session):
        self.db = db

    def add_team(self, team: schemas.TeamCreate):
        # TODO : save Team in database and get her ID
        db_team = models.Team(
            name=team.name,
            description=team.description,
            organization_id=team.organization_id,
        )
        self.db.add(db_team)
        self.db.commit()
        self.db.refresh(db_team)
        return db_team

    def get_one_team(self, team_id):
        """Find the team in database and return it

        :team_id: The id of the team to retreive.
        :returns: An Team in pyDantic BaseModel format.
        :rtype: schemas.Team
        """
        e = self.db.query(models.Team).filter(models.Team.id == team_id).first()
        if e is None:
            return None
        else:
            return self.get_db_to_class(e)

    def get_projects_from_team(self, team_id):
        # TODO : get Projects from Project id in database
        pass

    @staticmethod
    def get_db_to_class(team: models.Team) -> schemas.Team:
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

    def add_team(self, team: schemas.TeamCreate):
        self.teams.append(
            models.Team(
                id=self.id + 1,
                name=team.name,
                description=team.description,
                organization_id=team.organization_id,
            )
        )

    def get_one_team(self, team_id) -> schemas.Team:
        first_team = self.teams[0]
        return schemas.Team(
            id=first_team.id,
            name=first_team.name,
            description=first_team.description,
            organization_id=first_team.organization_id,
        )

    def get_projects_from_team(self, team_id):
        # TODO : get Projects from Project id in database
        pass

    @staticmethod
    def get_db_to_class(team: models.Team) -> schemas.Team:
        return schemas.Team(
            id=team.id,
            name=team.name,
            description=team.description,
            organization_id=team.organization_id,
        )
