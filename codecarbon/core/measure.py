from time import perf_counter

from codecarbon.core.units import Energy, Power
from codecarbon.external.hardware import CPU, GPU, AppleSiliconChip
from codecarbon.external.logger import logger
from codecarbon.external.ram import RAM


class MeasurePowerEnergy:
    """
    Measure power and energy consumption of a hardware component.
    """

    _last_measured_time: float = 0
    _hardware: list
    _pue: float
    _total_cpu_energy: Energy
    _total_gpu_energy: Energy
    _total_ram_energy: Energy
    _total_energy: Energy
    _cpu_power: Power
    _gpu_power: Power
    _ram_power: Power

    def __init__(self, hardware, pue):
        """
        :param hardware: list of hardware components to measure
        :param pue: Power Usage Effectiveness of the datacenter
        """
        self._last_measured_time = perf_counter()
        self._hardware = hardware
        self._pue = pue

        self._total_cpu_energy = Energy.from_energy(0)
        self._total_gpu_energy = Energy.from_energy(0)
        self._total_ram_energy = Energy.from_energy(0)
        self._total_energy = Energy.from_energy(0)

        self._cpu_power = Power.from_watts(0)
        self._gpu_power = Power.from_watts(0)
        self._ram_power = Power.from_watts(0)

    def do_measure(self) -> None:
        for hardware in self._hardware:
            h_time = perf_counter()
            # Compute last_duration again for more accuracy
            last_duration = perf_counter() - self._last_measured_time
            power, energy = hardware.measure_power_and_energy(
                last_duration=last_duration
            )
            # Apply the PUE of the datacenter to the consumed energy
            energy = Energy.from_energy(energy.kWh * self._pue)
            self._total_energy = Energy.from_energy(self._total_energy.kWh + energy.kWh)
            if isinstance(hardware, CPU):
                self._total_cpu_energy = Energy.from_energy(
                    self._total_cpu_energy.kWh + energy.kWh
                )
                self._cpu_power = power
                logger.info(
                    f"Energy consumed for all CPUs : {self._total_cpu_energy.kWh:.6f} kWh"
                    + f". Total CPU Power : {self._cpu_power.W} W"
                )
            elif isinstance(hardware, GPU):
                self._total_gpu_energy = Energy.from_energy(
                    self._total_gpu_energy.kWh + energy.kWh
                )
                self._gpu_power = power
                logger.info(
                    f"Energy consumed for all GPUs : {self._total_gpu_energy.kWh:.6f} kWh"
                    + f". Total GPU Power : {self._gpu_power.W} W"
                )
            elif isinstance(hardware, RAM):
                self._total_ram_energy = Energy.from_energy(
                    self._total_ram_energy.kWh + energy.kWh
                )
                self._ram_power = power
                logger.info(
                    f"Energy consumed for RAM : {self._total_ram_energy.kWh:.6f} kWh."
                    + f"RAM Power : {self._ram_power.W} W"
                )
            elif isinstance(hardware, AppleSiliconChip):
                if hardware.chip_part == "CPU":
                    self._total_cpu_energy = Energy.from_energy(
                        self._total_cpu_energy.kWh + energy.kWh
                    )
                    self._cpu_power = power
                    logger.info(
                        f"Energy consumed for AppleSilicon CPU : {self._total_cpu_energy.kWh:.6f} kWh"
                        + f".Apple Silicon CPU Power : {self._cpu_power.W} W"
                    )
                elif hardware.chip_part == "GPU":
                    self._total_gpu_energy = Energy.from_energy(
                        self._total_gpu_energy.kWh + energy.kWh
                    )
                    self._gpu_power = power
                    logger.info(
                        f"Energy consumed for AppleSilicon GPU : {self._total_gpu_energy.kWh:.6f} kWh"
                        + f".Apple Silicon GPU Power : {self._gpu_power.W} W"
                    )
            else:
                logger.error(f"Unknown hardware type: {hardware} ({type(hardware)})")
            h_time = perf_counter() - h_time
            logger.debug(
                f"{hardware.__class__.__name__} : {hardware.total_power().W:,.2f} "
                + f"W during {last_duration:,.2f} s [measurement time: {h_time:,.4f}]"
            )
        logger.info(
            f"{self._total_energy.kWh:.6f} kWh of electricity used since the beginning."
        )
