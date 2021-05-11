from typing import List
from carbonserver.api.domain.projects import Projects
from carbonserver.database import models, schemas
from sqlalchemy.orm import Session

"""
Here there is all the method to manipulate the project data
"""


class SqlAlchemyRepository(Projects):
    def __init__(self, db: Session):
        self.db = db

    def add_project(self, project: schemas.ProjectCreate):
        # TODO : save Project in database and get her ID
        db_project = models.Project(
            name=project.name,
            description=project.description,
            team_id=project.team_id,
        )
        self.db.add(db_project)
        self.db.commit()
        self.db.refresh(db_project)
        return db_project

    def get_one_project(self, project_id):
        # TODO : find the Project in database and return it
        pass


class InMemoryRepository(Projects):
    def __init__(self):
        self.projects: List = []
        self.id: int = 0
