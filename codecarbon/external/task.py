import time
from uuid import uuid4

from codecarbon.output import EmissionsData, TaskEmissionsData


class Task:
    """
    A task, used to segregate electrical consumption when executing a treatment.
    """

    is_active: bool
    emissions_data: EmissionsData

    def __init__(self, task_name):  # , task_measure
        self.task_id: str = task_name + uuid4().__str__()
        self.task_name: str = task_name
        self.start_time = time.perf_counter()
        self.is_active = True

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
            codecarbon_version=self.emissions_data.codecarbon_version,
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
