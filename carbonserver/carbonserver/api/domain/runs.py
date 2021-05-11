import abc
from carbonserver.database import schemas


class Runs(abc.ABC):
    @abc.abstractmethod
    def add_run(self, run: schemas.RunCreate):
        raise NotImplementedError
