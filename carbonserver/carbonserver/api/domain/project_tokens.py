import abc

from carbonserver.api import schemas


class ProjectTokens(abc.ABC):
    @abc.abstractmethod
    def add_project_token(self, project_id: str, project: schemas.ProjectTokenCreate):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_project_token(self, project_id: str, token_id: str):
        raise NotImplementedError

    @abc.abstractmethod
    def list_project_tokens(self, project_id: str):
        raise NotImplementedError
