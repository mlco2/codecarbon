"""
JSON output handler for CodeCarbon emissions data.

Writes emissions data as JSON to a file. Supports two modes:

- ``"append"`` (default): JSON Lines format — one JSON object per line,
  suitable for streaming / log-style output.
- ``"overwrite"``: Replaces the file with a single JSON object containing
  the latest run data for the given ``run_id``.
"""

import dataclasses
import json
import os
from typing import List

from codecarbon.external.logger import logger
from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.emissions_data import EmissionsData, TaskEmissionsData


class JSONOutput(BaseOutput):
    """
    Save emissions data to a JSON file.

    Attributes:
        output_file_name: Name of the JSON file to write to.
        output_dir: Directory path for the output file.
        on_json_write: Write mode — ``"append"`` for JSON Lines or
            ``"overwrite"`` to replace the file content.
    """

    def __init__(
        self,
        output_file_name: str = "emissions.json",
        output_dir: str = ".",
        on_json_write: str = "append",
    ):
        """
        Initialize the JSONOutput handler.

        Args:
            output_file_name: Name of the JSON output file.
            output_dir: Directory to write the file to.
            on_json_write: ``"append"`` for JSON Lines (one JSON object per
                line) or ``"overwrite"`` to replace the file with latest data.

        Raises:
            ValueError: If *on_json_write* is not ``"append"`` or ``"overwrite"``.
            OSError: If *output_dir* does not exist.
        """
        if on_json_write not in {"append", "overwrite"}:
            raise ValueError(
                f"Unknown `on_json_write` value: {on_json_write}"
                + " (should be one of 'append' or 'overwrite')"
            )
        self.output_file_name = output_file_name
        if not os.path.exists(output_dir):
            raise OSError(f"Folder '{output_dir}' doesn't exist !")
        self.output_dir = output_dir
        self.on_json_write = on_json_write
        self.save_file_path = os.path.join(self.output_dir, self.output_file_name)
        logger.info(
            f"JSON emissions data will be saved to {os.path.abspath(self.save_file_path)}"
        )

    def out(self, total: EmissionsData, _: EmissionsData):
        """
        Write total emissions data to a JSON file.

        In ``"append"`` mode, appends a new JSON line.
        In ``"overwrite"`` mode, replaces the file contents.

        Args:
            total: The total emissions data to write.
        """
        try:
            payload = dataclasses.asdict(total)
            if self.on_json_write == "append":
                with open(self.save_file_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(payload) + "\n")
            else:
                # overwrite mode: read existing data, update by run_id
                existing = self._read_existing_data()
                updated = False
                for i, entry in enumerate(existing):
                    if entry.get("run_id") == payload.get("run_id"):
                        existing[i] = payload
                        updated = True
                        break
                if not updated:
                    existing.append(payload)
                with open(self.save_file_path, "w", encoding="utf-8") as f:
                    json.dump(existing, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write JSON emissions data: {e}", exc_info=True)

    def live_out(self, total: EmissionsData, delta: EmissionsData):
        """
        Write live emissions data (periodic updates).

        Uses the same logic as :meth:`out`.
        """
        self.out(total, delta)

    def task_out(self, data: List[TaskEmissionsData], experiment_name: str):
        """
        Write task-level emissions data to a separate JSON file.

        The file is named ``emissions_{experiment_name}_{run_id}.json``.

        Args:
            data: List of task emissions data entries.
            experiment_name: Name of the experiment.
        """
        if not data:
            return
        try:
            run_id = data[0].run_id
            task_file_path = os.path.join(
                self.output_dir,
                f"emissions_{experiment_name}_{run_id}.json",
            )
            payload = [dataclasses.asdict(entry) for entry in data]
            with open(task_file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            logger.error(
                f"Failed to write JSON task emissions data: {e}", exc_info=True
            )

    def _read_existing_data(self) -> list:
        """Read existing JSON array from file, or return empty list."""
        if not os.path.isfile(self.save_file_path):
            return []
        try:
            with open(self.save_file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, OSError):
            logger.warning(
                f"Could not parse existing JSON file {self.save_file_path}. "
                "Starting fresh."
            )
            return []
