from carbonserver.api import schemas

import abc


class Project(abc.ABC):
    @abc.abstractmethod
    def save_project(self, project: schemas.ProjectCreate):
        raise NotImplementedError

    @abc.abstractmethod
    def get_one_project(self, project_id):
        raise NotImplementedError
