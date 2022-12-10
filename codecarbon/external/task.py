import time
from uuid import uuid4

from codecarbon.core.units import Energy
from codecarbon.output import EmissionsData


class Task:
    """
    A task, used to segregate electrical consumption when executing a treatment.
    """

    _final_cpu_energy: Energy
    _final_gpu_energy: Energy
    _final_ram_energy: Energy
    is_active: bool
    emissions_data: EmissionsData

    def __init__(
        self, task_name, intial_cpu_energy, intial_gpu_energy, intial_ram_energy
    ):
        self.task_id = uuid4()
        self.task_name = task_name
        self._initial_cpu_energy: Energy = intial_cpu_energy
        self._initial_gpu_energy: Energy = intial_gpu_energy
        self._initial_ram_energy: Energy = intial_ram_energy
        self.start_time = time.time()
        self.is_active = True

    def compute_final_cpu_energy(self, current_cpu_energy):
        return current_cpu_energy - self._initial_cpu_energy

    def compute_final_gpu_energy(self, current_gpu_energy):
        return current_gpu_energy - self._initial_gpu_energy

    def compute_final_ram_energy(self, current_ram_energy):
        return current_ram_energy - self._initial_ram_energy
