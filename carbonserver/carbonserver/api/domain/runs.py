import abc

from carbonserver.api import schemas


class Runs(abc.ABC):
    @abc.abstractmethod
    def add_run(self, run: schemas.RunCreate):
        raise NotImplementedError
