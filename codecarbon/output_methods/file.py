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

    Attributes:
        output_file_name: str, name of file to write to.
        output_dir: str, path to directory to write to.
        save_file_path: str, path to file to write to.
        on_csv_write: str, "append" or "update", whether or not to append or overwrite a file if it exists.
    """

    def __init__(
        self,
        output_file_name: str,
        output_dir: str,
        on_csv_write: str = "append",
        enable_live_out: bool = False,
    ):
        """
        Initialize the FileOutput object.

        Args:
            output_file_name: name of file to write to.
            output_dir: path to directory to write to.
            on_csv_write: "append" or "update", whether or not to append or overwrite a file if it exists
            enable_live_out: when True, also write on live measurement intervals
                (same cadence as API/Prometheus: ``api_call_interval * measure_power_secs``).

        Raises:
            ValueError: If the on_csv_write value is invalid.
            OSError: If the output directory does not exist.
        """
        if on_csv_write not in {"append", "update"}:
            raise ValueError(
                f"Unknown `on_csv_write` value: {on_csv_write}"
                + " (should be one of 'append' or 'update'"
            )
        self.output_file_name: str = output_file_name
        if not os.path.exists(output_dir):
            raise OSError(f"Folder '{output_dir}' doesn't exist !")
        self.output_dir: str = output_dir
        self.on_csv_write: str = on_csv_write
        self.enable_live_out: bool = enable_live_out
        self.save_file_path = os.path.join(self.output_dir, self.output_file_name)
        logger.info(
            f"Emissions data (if any) will be saved to file {os.path.abspath(self.save_file_path)}"
        )

    def has_valid_headers(self, data: EmissionsData) -> bool:
        """
        Checks self.save_file_path has headers matching those from passed data.

        Args:
            data: EmissionsData object with valid headers.

        Returns:
            True if the file has valid headers, False otherwise.
        """
        with open(self.save_file_path) as csv_file:
            reader = csv.reader(csv_file)
            try:
                headers = next(reader)
            except StopIteration:
                return True
            return sorted(headers) == sorted(data.values.keys())

    def live_out(self, total: EmissionsData, delta: EmissionsData):
        """Write a measurement row on the live interval when enabled."""
        if self.enable_live_out:
            self.out(total, delta)

    def out(self, total: EmissionsData, _):
        """
        Save the emissions data from a whole run to a CSV file.

        * If the file does not exist, then create it.
        * If the file already exists but has invalid headers, then back it up and replace with new data.
        * If the file already exists and has valid headers:
            * In "append" mode, append the new row directly.
            * In "update" mode, deduplicate by run_id.

        Args:
            total: data to save.


        """
        file_exists: bool = os.path.isfile(self.save_file_path)
        if file_exists and os.path.getsize(self.save_file_path) == 0:
            logger.warning(
                f"File {self.save_file_path} exists but is empty. Treating as new file."
            )
            file_exists = False

        headers_match = file_exists and self.has_valid_headers(total)
        if file_exists and not headers_match:
            logger.warning("The CSV format has changed, backing up old emission file.")
            backup(self.save_file_path)
            file_exists = False

        new_df = pd.DataFrame.from_records([dict(total.values)])

        if not file_exists:
            new_df.to_csv(self.save_file_path, index=False)
        elif self.on_csv_write == "append":
            new_df = new_df.dropna(axis=1, how="all")
            new_df.to_csv(self.save_file_path, mode="a", header=False, index=False)
        else:
            df = pd.read_csv(self.save_file_path)
            df_run = df.loc[df.run_id == total.run_id]
            if len(df_run) < 1:
                df = pd.concat([df, new_df])
            elif len(df_run) > 1:
                logger.warning(
                    f"CSV contains more than 1 ({len(df_run)})"
                    + f" rows with current run ID ({total.run_id})."
                    + "Appending instead of updating."
                )
                df = pd.concat([df, new_df])
            else:
                update_values = {}
                for col, val in dict(total.values).items():
                    update_values[col] = df[col].dtype.type(val)
                df.loc[df.run_id == total.run_id, update_values.keys()] = (
                    update_values.values()
                )
            df.to_csv(self.save_file_path, index=False)

    def task_out(self, data: List[TaskEmissionsData], experiment_name: str):
        """
        Save the emissions data from a single task in an experiment run to a CSV file.

        Does not attempt to backup existing files or prevent overwriting them.
        """
        run_id = data[0].run_id
        save_task_file_path = os.path.join(
            self.output_dir, "emissions_" + experiment_name + "_" + run_id + ".csv"
        )
        new_df = pd.DataFrame.from_records(
            [dict(data_point.values) for data_point in data]
        )
        # Filter out empty or all-NA columns only from new_df, to avoid warnings from Pandas
        # see https://github.com/pandas-dev/pandas/issues/55928
        new_df = new_df.dropna(axis=1, how="all")
        df = new_df
        df.to_csv(save_task_file_path, index=False)
