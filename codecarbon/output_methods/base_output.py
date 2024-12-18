from typing import List

from codecarbon.output_methods.emissions_data import EmissionsData, TaskEmissionsData


class BaseOutput:
    """
    An abstract class defining possible contracts for an output strategy, a strategy implementation can save emissions
    data to a file, posting to Json Box, saving to a database, sending a Slack message etc.
    Each method is responsible for a different part of the EmissionsData lifecycle:
        - `out` is used by termination calls such as emissions_tracker.flush and emissions_tracker.stop
        - `live_out` is used by live measurement events, e.g. the iterative update of prometheus metrics
        - `task_out` is used by terminate calls such as emissions_tracker.flush and emissions_tracker.stop, but uses
          emissions segregated by task
    """

    def out(self, total: EmissionsData, delta: EmissionsData):
        pass

    def live_out(self, total: EmissionsData, delta: EmissionsData):
        pass

    def task_out(self, data: List[TaskEmissionsData], experiment_name: str):
        pass
