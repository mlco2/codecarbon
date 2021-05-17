from carbonserver.database import models, schemas
import abc


class Projects(abc.ABC):
    @abc.abstractmethod
    def add_project(self, project: schemas.ProjectCreate):
        raise NotImplementedError

    @abc.abstractmethod
    def get_db_to_class(self, project: models.Project) -> schemas.Project:
        raise NotImplementedError

    @abc.abstractmethod
    def get_one_project(self, project_id):
        raise NotImplementedError
