import abc

from carbonserver.api import schemas


class Teams(abc.ABC):
    @abc.abstractmethod
    def add_team(self, team: schemas.TeamCreate):
        raise NotImplementedError

    @abc.abstractmethod
    def get_one_team(self, team_id):
        raise NotImplementedError

    @abc.abstractmethod
    def list_teams(self):
        raise NotImplementedError
