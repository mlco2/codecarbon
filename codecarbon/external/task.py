import time
from uuid import uuid4

from codecarbon.core.units import Energy
from codecarbon.output import EmissionsData, TaskEmissionsData


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
        self.task_id: str = task_name + uuid4().__str__()
        self.task_name: str = task_name
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

    def out(self):
        return TaskEmissionsData(
            task_name=self.task_name,
            timestamp=self.emissions_data.timestamp,
            project_name=self.emissions_data.project_name,
            run_id=self.emissions_data.run_id,
            duration=self.emissions_data.duration,
            emissions=self.emissions_data.emissions,
            emissions_rate=self.emissions_data.emissions_rate,
            cpu_power=self.emissions_data.cpu_power,
            gpu_power=self.emissions_data.gpu_power,
            ram_power=self.emissions_data.ram_power,
            cpu_energy=self.emissions_data.cpu_energy,
            gpu_energy=self.emissions_data.gpu_energy,
            ram_energy=self.emissions_data.ram_energy,
            energy_consumed=self.emissions_data.energy_consumed,
            country_name=self.emissions_data.country_name,
            country_iso_code=self.emissions_data.country_iso_code,
            region=self.emissions_data.region,
            cloud_provider=self.emissions_data.cloud_provider,
            cloud_region=self.emissions_data.cloud_region,
            os=self.emissions_data.os,
            python_version=self.emissions_data.python_version,
            cpu_count=self.emissions_data.cpu_count,
            cpu_model=self.emissions_data.cpu_model,
            gpu_count=self.emissions_data.gpu_count,
            gpu_model=self.emissions_data.gpu_model,
            longitude=self.emissions_data.longitude,
            latitude=self.emissions_data.latitude,
            ram_total_size=self.emissions_data.ram_total_size,
            tracking_mode=self.emissions_data.tracking_mode,
            on_cloud=self.emissions_data.on_cloud,
        )
