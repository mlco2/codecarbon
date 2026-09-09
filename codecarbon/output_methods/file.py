import csv
import math
import os
from typing import List

from codecarbon.core.util import backup
from codecarbon.external.logger import logger
from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData, TaskEmissionsData


def _as_csv_row(values: dict) -> dict:
    """Render a data row as strings, with missing values as empty cells.

    Any non-finite float (NaN, +inf, -inf) is written as an empty cell. NaN
    matches what pandas' ``to_csv`` did; infinities are a deliberate
    divergence (``to_csv`` wrote the literal "inf") because an infinite
    energy or emissions value is not a real measurement, and an empty cell
    reads back as missing instead of poisoning downstream arithmetic.
    """
    return {
        k: (
            ""
            if v is None or (isinstance(v, float) and not math.isfinite(v))
            else str(v)
        )
        for k, v in values.items()
    }


def _write_rows(path: str, fieldnames: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="") as csv_file:
        # extrasaction="ignore" is defensive only: a row can never carry a key
        # outside `fieldnames`, because `out()` backs the file up and rewrites it
        # from scratch whenever `has_valid_headers()` reports a mismatch.
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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
        self, output_file_name: str, output_dir: str, on_csv_write: str = "append"
    ):
        """
        Initialize the FileOutput object.

        Args:
            output_file_name: name of file to write to.
            output_dir: path to directory to write to.
            on_csv_write: "append" or "update", whether or not to append or overwrite a file if it exists

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

        new_row = _as_csv_row(dict(total.values))

        if not file_exists:
            _write_rows(self.save_file_path, list(new_row), [new_row])
        elif self.on_csv_write == "append":
            # Use the header already on disk as the column order: the row dict's
            # key order is not guaranteed to match it (has_valid_headers()
            # compares the two sorted), and trusting it would misalign columns.
            with open(self.save_file_path, newline="") as csv_file:
                fieldnames = next(csv.reader(csv_file), None)
            if not fieldnames:
                _write_rows(self.save_file_path, list(new_row), [new_row])
            else:
                with open(self.save_file_path, "a", newline="") as csv_file:
                    csv.DictWriter(
                        csv_file, fieldnames=fieldnames, extrasaction="ignore"
                    ).writerow(new_row)
        else:
            with open(self.save_file_path, newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                fieldnames = reader.fieldnames or list(new_row)
                rows = list(reader)
            matching = [r for r in rows if r.get("run_id") == str(total.run_id)]
            if len(matching) > 1:
                logger.warning(
                    f"CSV contains more than 1 ({len(matching)})"
                    + f" rows with current run ID ({total.run_id})."
                    + "Appending instead of updating."
                )
            if len(matching) == 1:
                matching[0].update(new_row)
            else:
                rows.append(new_row)
            _write_rows(self.save_file_path, fieldnames, rows)

    def task_out(self, data: List[TaskEmissionsData], experiment_name: str):
        """
        Save the emissions data from a single task in an experiment run to a CSV file.

        Does not attempt to backup existing files or prevent overwriting them.
        """
        run_id = data[0].run_id
        save_task_file_path = os.path.join(
            self.output_dir, "emissions_" + experiment_name + "_" + run_id + ".csv"
        )
        rows = [_as_csv_row(dict(data_point.values)) for data_point in data]
        # Drop columns that are empty in every row, matching the previous
        # dropna(axis=1, how="all").
        fieldnames = [
            column for column in rows[0] if any(row.get(column) != "" for row in rows)
        ]
        _write_rows(save_task_file_path, fieldnames, rows)
