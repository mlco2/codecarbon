from carbonserver.api.domain.teams import Teams
from carbonserver.database import models, schemas
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
        )
        self.db.add(db_team)
        self.db.commit()
        self.db.refresh(db_team)
        return db_team

    def get_one_team(self, team_id):
        # TODO : find the Team in database and return it
        pass

    def get_projects_from_team(self, team_id):
        # TODO : get Projects from Project id in database
        pass
