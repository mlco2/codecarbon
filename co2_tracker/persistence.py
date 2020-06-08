""" Provides functionality for persistence of data """

import csv
import os
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CO2Data:
    """ Encapsulates experiment artifacts
    """

    timestamp: datetime
    experiment_id: str
    project_name: str
    duration: float
    emissions: float

    @property
    def values(self) -> OrderedDict:
        return OrderedDict(
            [
                ("timestamp", self.timestamp.strftime("%Y-%m-%d %H:%M:%S")),
                ("experiment_id", self.experiment_id),
                ("project_name", self.project_name),
                ("duration", str(self.duration)),
                ("emissions", str(self.emissions)),
            ]
        )


class BasePersistence(ABC):
    """ An abstract class that requires children to inherit a single method,
    `flush` which is used for persisting data. This could be by saving it to a file,
    posting to Json Box, saving to a database, sending a slack message etc.
    """

    @abstractmethod
    def flush(self, data: CO2Data):
        pass


class FilePersistence(BasePersistence):
    """ Saves experiment artifacts to a file
    """

    def __init__(self, save_file_path: str):
        self.save_file_path: str = save_file_path

    def flush(self, data: CO2Data):
        file_exists: bool = os.path.isfile(self.save_file_path)

        with open(self.save_file_path, "a+") as f:
            writer = csv.DictWriter(f, fieldnames=data.values.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data.values)
