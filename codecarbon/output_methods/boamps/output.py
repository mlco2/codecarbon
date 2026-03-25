"""
BoAmps output handler for CodeCarbon.

Writes BoAmps-formatted JSON reports containing energy consumption data
from CodeCarbon runs, enriched with user-provided ML task context.
"""

import json
import os
from typing import Optional

from codecarbon.external.logger import logger
from codecarbon.output_methods.base_output import BaseOutput
from codecarbon.output_methods.boamps.mapper import map_emissions_to_boamps
from codecarbon.output_methods.boamps.models import (
    BoAmpsHardware,
    BoAmpsHeader,
    BoAmpsTask,
    camel_to_snake,
)
from codecarbon.output_methods.emissions_data import EmissionsData


def _extract_overrides(data: dict, keys: tuple) -> dict:
    """Extract known camelCase keys from a dict, returning them as snake_case."""
    return {camel_to_snake(k): data[k] for k in keys if k in data}


class BoAmpsOutput(BaseOutput):
    """
    Output handler that writes BoAmps-formatted JSON reports.

    BoAmps (by Boavizta) is a standardized JSON format for reporting
    AI/ML energy consumption. This handler auto-fills measurable fields
    from CodeCarbon's EmissionsData and merges user-provided context
    (task description, algorithms, datasets, etc.).

    Usage:
        # Programmatic
        handler = BoAmpsOutput(
            task=BoAmpsTask(task_stage="inference", task_family="chatbot", ...),
            quality="high",
        )
        tracker = EmissionsTracker(output_handlers=[handler])

        # From context file
        handler = BoAmpsOutput.from_file("boamps_context.json")
        tracker = EmissionsTracker(output_handlers=[handler])
    """

    def __init__(
        self,
        output_dir: str = ".",
        task: Optional[BoAmpsTask] = None,
        header: Optional[BoAmpsHeader] = None,
        quality: Optional[str] = None,
        infra_overrides: Optional[dict] = None,
        environment_overrides: Optional[dict] = None,
    ):
        self._output_dir = output_dir
        self._task = task
        self._header = header
        self._quality = quality
        self._infra_overrides = infra_overrides
        self._environment_overrides = environment_overrides

    @classmethod
    def from_file(cls, context_file_path: str, output_dir: str = ".") -> "BoAmpsOutput":
        """
        Load BoAmps context from a JSON file.

        The context file should follow the BoAmps report schema structure,
        containing fields that cannot be auto-detected by CodeCarbon
        (e.g., task, publisher, quality).

        Args:
            context_file_path: Path to the BoAmps context JSON file.
            output_dir: Directory to write output reports to.

        Returns:
            A configured BoAmpsOutput instance.

        Raises:
            FileNotFoundError: If the context file does not exist.
            json.JSONDecodeError: If the context file contains invalid JSON.
        """
        try:
            with open(context_file_path) as f:
                context = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"BoAmps context file not found: {context_file_path}"
            )

        task = None
        header = None
        quality = None
        infra_overrides = None
        environment_overrides = None

        if "task" in context:
            task = BoAmpsTask.from_dict(context["task"])

        if "header" in context:
            header = BoAmpsHeader.from_dict(context["header"])

        if "quality" in context:
            quality = context["quality"]

        if "infrastructure" in context:
            infra_overrides = _extract_overrides(
                context["infrastructure"],
                ("cloudInstance", "cloudService", "infraType"),
            )
            # Preserve user-provided components (manufacturer, family, series, etc.)
            if "components" in context["infrastructure"]:
                infra_overrides["components"] = [
                    BoAmpsHardware.from_dict(c)
                    for c in context["infrastructure"]["components"]
                ]

        if "environment" in context:
            environment_overrides = _extract_overrides(
                context["environment"],
                (
                    "location",
                    "powerSupplierType",
                    "powerSource",
                    "powerSourceCarbonIntensity",
                ),
            )

        return cls(
            output_dir=output_dir,
            task=task,
            header=header,
            quality=quality,
            infra_overrides=infra_overrides,
            environment_overrides=environment_overrides,
        )

    def out(self, total: EmissionsData, delta: EmissionsData):
        """Write the final BoAmps report as a JSON file."""
        try:
            report = map_emissions_to_boamps(
                total,
                task=self._task,
                header=self._header,
                quality=self._quality,
                infra_overrides=self._infra_overrides,
                environment_overrides=self._environment_overrides,
            )
            report_dict = report.to_dict()
            file_name = f"boamps_report_{total.run_id}.json"
            file_path = os.path.join(self._output_dir, file_name)
            with open(file_path, "w") as f:
                json.dump(report_dict, f, indent=2)
            logger.info(f"BoAmps report saved to {os.path.abspath(file_path)}")
        except Exception as e:
            logger.error(f"Failed to write BoAmps report: {e}", exc_info=True)

    def live_out(self, total: EmissionsData, delta: EmissionsData):
        """No-op: BoAmps reports are final, not incremental."""
