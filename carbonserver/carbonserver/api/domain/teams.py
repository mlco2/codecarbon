from carbonserver.database import schemas

import abc


class Teams(abc.ABC):
    @abc.abstractmethod
    def add_team(self, team: schemas.TeamCreate):
        raise NotImplementedError

    @abc.abstractmethod
    def get_one_team(self, team_id):
        raise NotImplementedError

    @abc.abstractmethod
    def get_projects_from_team(self, team_id):
        raise NotImplementedError
