import csv
import os
from typing import List

import pandas as pd

from codecarbon.core.util import backup
from codecarbon.external.logger import logger
from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData, TaskEmissionsData


class FileOutput(BaseOutput):
    """
    Saves experiment artifacts to a file
    """

    def __init__(self, save_file_path: str, on_csv_write: str = "append"):
        if on_csv_write not in {"append", "update"}:
            raise ValueError(
                f"Unknown `on_csv_write` value: {on_csv_write}"
                + " (should be one of 'append' or 'update'"
            )
        self.on_csv_write: str = on_csv_write
        self.save_file_path: str = save_file_path
        logger.info(
            f"Saving emissions data to file {os.path.abspath(self.save_file_path)}"
        )

    def has_valid_headers(self, data: EmissionsData):
        with open(self.save_file_path) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            dict_from_csv = dict(list(csv_reader)[0])
            list_of_column_names = list(dict_from_csv.keys())
            return list(data.values.keys()) == list_of_column_names

    def out(self, data: EmissionsData):
        file_exists: bool = os.path.isfile(self.save_file_path)
        if file_exists and not self.has_valid_headers(data):
            logger.info("Backing up old emission file")
            backup(self.save_file_path)
            file_exists = False

        if not file_exists:
            df = pd.DataFrame(columns=data.values.keys())
            df = pd.concat([df, pd.DataFrame.from_records([dict(data.values)])])
        elif self.on_csv_write == "append":
            df = pd.read_csv(self.save_file_path)
            df = pd.concat([df, pd.DataFrame.from_records([dict(data.values)])])
        else:
            df = pd.read_csv(self.save_file_path)
            df_run = df.loc[df.run_id == data.run_id]
            if len(df_run) < 1:
                df = pd.concat([df, pd.DataFrame.from_records([dict(data.values)])])
            elif len(df_run) > 1:
                logger.warning(
                    f"CSV contains more than 1 ({len(df_run)})"
                    + f" rows with current run ID ({data.run_id})."
                    + "Appending instead of updating."
                )
                df = pd.concat([df, pd.DataFrame.from_records([dict(data.values)])])
            else:
                df.at[df.run_id == data.run_id, data.values.keys()] = (
                    data.values.values()
                )

        df.to_csv(self.save_file_path, index=False)

    def task_out(self, data: List[TaskEmissionsData], experiment_name: str, output_dir):
        run_id = data[0].run_id
        save_task_file_path = os.path.join(
            output_dir, "emissions_" + experiment_name + "_" + run_id + ".csv"
        )
        df = pd.DataFrame(columns=data[0].values.keys())
        df = pd.concat(
            [
                df,
                pd.DataFrame.from_records(
                    [dict(data_point.values) for data_point in data]
                ),
            ]
        )
        df.to_csv(save_task_file_path, index=False)
