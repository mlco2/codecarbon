import csv
import os
import threading
from typing import List, Optional

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
        # live_out runs on the scheduler thread, flush() and stop() call out()
        # on the caller's thread: one write at a time.
        self._write_lock = threading.RLock()
        self.save_file_path = os.path.join(self.output_dir, self.output_file_name)
        logger.info(
            f"Emissions data (if any) will be saved to file {os.path.abspath(self.save_file_path)}"
        )

    def has_valid_headers(
        self, data: EmissionsData, headers: Optional[List[str]] = None
    ) -> bool:
        """
        Checks self.save_file_path has headers matching those from passed data.

        Args:
            data: EmissionsData object with valid headers.
            headers: header row already read from the file; read it if None.

        Returns:
            True if the file has valid headers, False otherwise.
        """
        if headers is None:
            headers = self._read_headers()
            if headers is None:
                return True
        return sorted(headers) == sorted(data.values.keys())

    def _read_headers(self) -> Optional[List[str]]:
        """
        Read the header row of self.save_file_path, or None if the file is empty.
        """
        with open(self.save_file_path, newline="") as csv_file:
            return next(csv.reader(csv_file), None)

    def live_out(self, total: EmissionsData, delta: EmissionsData):
        """
        Write a measurement row on the live interval when enabled.

        A failed write (file locked, disk full...) is logged, not raised: the
        tracker calls every handler's live_out in turn, and an exception here
        would skip the API and Prometheus outputs after this one. The next
        interval tries again.
        """
        if not self.enable_live_out:
            return
        try:
            self.out(total, delta)
        except Exception as e:
            logger.error(f"Could not write interval CSV {self.save_file_path}: {e}")

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
        with self._write_lock:
            self._write_row(total)

    def _write_row(self, total: EmissionsData):
        file_exists: bool = os.path.isfile(self.save_file_path)
        if file_exists and os.path.getsize(self.save_file_path) == 0:
            logger.warning(
                f"File {self.save_file_path} exists but is empty. Treating as new file."
            )
            file_exists = False

        headers = self._read_headers() if file_exists else None
        headers_match = file_exists and self.has_valid_headers(total, headers)
        if file_exists and not headers_match:
            logger.warning("The CSV format has changed, backing up old emission file.")
            backup(self.save_file_path)
            file_exists = False

        new_df = pd.DataFrame.from_records([dict(total.values)])

        if not file_exists:
            new_df.to_csv(self.save_file_path, index=False)
        elif self.on_csv_write == "append":
            # Never drop all-NA columns here: the append is headerless, so column
            # identity is positional and a missing column shifts every value after it.
            # Header names may be in any order (see has_valid_headers), so write the
            # values in the file's order. reindex() drops or NaN-fills mismatched
            # columns silently: it is only safe because has_valid_headers() above
            # guarantees the file and the record have the same set of columns.
            new_df = new_df.reindex(columns=headers)
            new_df.to_csv(self.save_file_path, mode="a", header=False, index=False)
        else:
            df = pd.read_csv(self.save_file_path)
            df_run = df.loc[df.run_id == total.run_id]
            if len(df_run) > 1:
                logger.warning(
                    f"CSV contains more than 1 ({len(df_run)})"
                    + f" rows with current run ID ({total.run_id})."
                    + "Appending instead of updating."
                )
                df = pd.concat([df, new_df])
            else:
                # Drop the previous row for this run (if any) and re-append it.
                # Assigning column by column would coerce values to the dtype
                # pandas inferred for the existing column, which breaks for
                # columns that are empty in every row (read back as float64).
                df = pd.concat([df.loc[df.run_id != total.run_id], new_df])
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


class IntervalFileOutput(FileOutput):
    """
    Separate CSV of the interval export (``csv_run_name``): a row is appended on
    every live interval, and at each flush() and stop().
    """

    def __init__(
        self, output_file_name: str, output_dir: str, name_after_run_id: bool = False
    ):
        """
        Args:
            output_file_name: name of file to write to.
            output_dir: path to directory to write to.
            name_after_run_id: write to ``emissions_<run_id>.csv``, with the
                run_id of each row. start() can replace the local run_id by the
                API run id after this output is built, and the file follows it.
        """
        super().__init__(
            output_file_name, output_dir, on_csv_write="append", enable_live_out=True
        )
        self.name_after_run_id = name_after_run_id

    @staticmethod
    def run_file_name(run_id) -> str:
        return f"emissions_{run_id}.csv"

    def out(self, total: EmissionsData, delta: EmissionsData):
        with self._write_lock:
            if self.name_after_run_id:
                self.output_file_name = self.run_file_name(total.run_id)
                self.save_file_path = os.path.join(
                    self.output_dir, self.output_file_name
                )
            super().out(total, delta)

    def task_out(self, data: List[TaskEmissionsData], experiment_name: str):
        """
        Task CSVs belong to the primary CSV output: writing them here would
        create them when only csv_run_name was set, or write them twice.
        """
