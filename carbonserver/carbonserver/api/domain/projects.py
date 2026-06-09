import abc

from carbonserver.api import schemas


class Projects(abc.ABC):
    @abc.abstractmethod
    def add_project(self, project: schemas.ProjectCreate):
        raise NotImplementedError

    @abc.abstractmethod
    def get_one_project(self, project_id):
        raise NotImplementedError
