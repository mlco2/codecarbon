from abc import ABC, abstractmethod

from codecarbon.output_methods.emissions_data import EmissionsData


class BaseOutput(ABC):
    """
    An abstract class that requires children to inherit a single method,
    `out` which is used for persisting data. This could be by saving it to a file,
    posting to Json Box, saving to a database, sending a slack message etc.

    if use_emissions_delta is True, the output method will only send/receive the delta of the emissions (emissions - previous_emissions)
    Else, the output method will send/receive the total emissions
    """

    use_emissions_delta = False

    @abstractmethod
    def out(self, data: EmissionsData):
        pass
