from typing import List

from sqlalchemy.orm import Session

from carbonserver.api import schemas
from carbonserver.api.domain.projects import Projects
from carbonserver.database import models

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
        """Find the projet in database and return it

        :project_id: The id of the experiment to retreive.
        :returns: An Project in pyDantic BaseModel format.
        :rtype: schemas.Project
        """
        e = (
            self.db.query(models.Project)
            .filter(models.Project.id == project_id)
            .first()
        )
        if e is None:
            return None
        else:
            return self.get_db_to_class(e)

        # TODO : find the Project in database and return it
        # pass

    @staticmethod
    def get_db_to_class(project: models.Project) -> schemas.Project:
        """Convert a models.Project to a schemas.Project

        :project: An Project in SQLAlchemy format.
        :returns: An Project in pyDantic BaseModel format.
        :rtype: schemas.Project
        """
        return schemas.Project(
            id=project.id,
            name=project.name,
            description=project.description,
            # isactive=experiment.is_active,
            team_id=project.team_id,
        )


class InMemoryRepository(Projects):
    def __init__(self):
        self.projects: List = []
        self.id: int = 0

    def add_project(self, project: schemas.ProjectCreate):
        self.projects.append(
            models.Project(
                id=self.id + 1,
                name=project.name,
                description=project.description,
                team_id=project.team_id,
            )
        )

    def get_one_project(self, project_id) -> schemas.Project:
        first_project = self.projects[0]
        return schemas.Project(
            id=first_project.id,
            name=first_project.name,
            description=first_project.description,
            team_id=first_project.team_id,
        )

    @staticmethod
    def get_db_to_class(self, project: models.Project) -> schemas.Project:
        return schemas.Project(
            id=project.id,
            name=project.name,
            description=project.description,
            team_id=project.team_id,
        )
