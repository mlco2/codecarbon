"""
Contains implementations of the Public facing API: EmissionsTracker,
OfflineEmissionsTracker and @track_emissions
"""

import dataclasses
import os
import platform
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from codecarbon._version import __version__
from codecarbon.core.config import get_hierarchical_config
from codecarbon.core.emissions import Emissions
from codecarbon.core.resource_tracker import ResourceTracker
from codecarbon.core.units import Energy, Power, Time
from codecarbon.core.util import count_cpus, suppress
from codecarbon.external.geography import CloudMetadata, GeoMetadata
from codecarbon.external.hardware import CPU, GPU, RAM, AppleSiliconChip
from codecarbon.external.logger import logger, set_logger_format, set_logger_level
from codecarbon.external.scheduler import PeriodicScheduler
from codecarbon.external.task import Task
from codecarbon.input import DataSource
from codecarbon.lock import Lock
from codecarbon.output import (
    BaseOutput,
    CodeCarbonAPIOutput,
    EmissionsData,
    FileOutput,
    HTTPOutput,
    LogfireOutput,
    LoggerOutput,
    PrometheusOutput,
)

# /!\ Warning: current implementation prevents the user from setting any value to None
# from the script call
# Imagine:
#   1/ emissions_endpoint=localhost:8000 in ~/.codecarbon.config
#   2/ Inside the script, the user cannot disable emissions_endpoint with
#   EmissionsTracker(emissions_endpoint=None) since the config logic will use the one in
#   the config file.
#
# Alternative: EmissionsTracker(emissions_endpoint=False) would work
# TODO: document this
#
# To fix this, a complex move would be to have default values set to the sentinel:
# _sentinel = object()
# see: https://stackoverflow.com/questions/67202314/
#      python-distinguish-default-argument-and-argument-provided-with-default-value

_sentinel = object()


class BaseEmissionsTracker(ABC):
    """
    Primary abstraction with Emissions Tracking functionality.
    Has two abstract methods, `_get_geo_metadata` and `_get_cloud_metadata`
    that are implemented by two concrete classes: `OfflineEmissionTracker`
    and `EmissionTracker.`
    """

    def _set_from_conf(
        self, var, name, default=None, return_type=None, prevent_setter=False
    ):
        """
        Method to standardize private argument setting. Generic flow is:

        * If a value for the variable `var` with name `name` is provided in the
          __init__ constructor: set the the private attribute `self._{name}` to
          that value

        * If no value is provided for `var`, i.e. `var is _sentinel` is True then
          we try to assign a value to it:

            * If there is a value for `name` in the external configuration (config
              files or env variables), then we use it
            * Otherwise `self._{name}` is set to the `default` value

        Additionally, if `return_type` is provided and one of `float` `int` or `bool`,
        the value for `self._{name}` will be parsed to this type.

        Use `prevent_setter=True` for debugging purposes only.

        Args:
            var (Any): The variable's value to set as private attribute
            name (str): The variable's name such that `self._{name}` will be set
                to `var`
            default (Any, optional): The value to use for self._name if no value
                is provided in the constructor and no value is found in the external
                configuration.
                Defaults to None.
            return_type (Any, optional): A type to parse the value to. Defaults to None.
            prevent_setter (bool, optional): Whether to set the private attribute or
                simply return the value. For debugging. Defaults to False.

        Returns:
            [Any]: The value used for `self._{name}`
        """
        # Check the hierarchical configuration has been read parsed and set.
        assert hasattr(self, "_external_conf")
        assert isinstance(self._external_conf, dict)

        # Store final values in _conf
        if not hasattr(self, "_conf"):
            self._conf = {"codecarbon_version": __version__}

        value = _sentinel

        # a value for the keyword argument `name` is provided in the constructor:
        # use it
        if var is not _sentinel:
            value = var
        else:
            # no value provided in the constructor for `name`: check in the conf
            # (using the provided default value)
            value = self._external_conf.get(name, default)

            # parse to `return_type` if needed
            if return_type is not None:
                if return_type is bool:
                    value = str(value).lower() == "true"
                else:
                    assert callable(return_type)
                    value = return_type(value)
        # Check conf
        if name == "output_dir":
            if not os.path.exists(value):
                raise OSError(f"Folder '{value}' doesn't exist !")
        if name == "gpu_ids":
            if value is None and os.environ.get("CUDA_VISIBLE_DEVICES"):
                value = os.environ.get("CUDA_VISIBLE_DEVICES")
        # store final value
        self._conf[name] = value
        # set `self._{name}` to `value`
        if not prevent_setter:
            setattr(self, f"_{name}", value)
        # return final value (why not?)
        return value

    def __init__(
        self,
        project_name: Optional[str] = _sentinel,
        measure_power_secs: Optional[float] = _sentinel,
        api_call_interval: Optional[int] = _sentinel,
        api_endpoint: Optional[str] = _sentinel,
        api_key: Optional[str] = _sentinel,
        output_dir: Optional[str] = _sentinel,
        output_file: Optional[str] = _sentinel,
        save_to_file: Optional[bool] = _sentinel,
        save_to_api: Optional[bool] = _sentinel,
        save_to_logger: Optional[bool] = _sentinel,
        logging_logger: Optional[LoggerOutput] = _sentinel,
        save_to_prometheus: Optional[bool] = _sentinel,
        save_to_logfire: Optional[bool] = _sentinel,
        prometheus_url: Optional[str] = _sentinel,
        output_handlers: Optional[List[BaseOutput]] = _sentinel,
        gpu_ids: Optional[List] = _sentinel,
        emissions_endpoint: Optional[str] = _sentinel,
        experiment_id: Optional[str] = _sentinel,
        experiment_name: Optional[str] = _sentinel,
        co2_signal_api_token: Optional[str] = _sentinel,
        tracking_mode: Optional[str] = _sentinel,
        log_level: Optional[Union[int, str]] = _sentinel,
        on_csv_write: Optional[str] = _sentinel,
        logger_preamble: Optional[str] = _sentinel,
        default_cpu_power: Optional[int] = _sentinel,
        pue: Optional[int] = _sentinel,
        allow_multiple_runs: Optional[bool] = _sentinel,
    ):
        """
        :param project_name: Project name for current experiment run, default name
                             is "codecarbon".
        :param measure_power_secs: Interval (in seconds) to measure hardware power
                                   usage, defaults to 15.
        :param api_call_interval: Occurrence to wait before calling API :
                            -1 : only call api on flush() and at the end.
                            1 : at every measure
                            2 : every 2 measure, etc...
        :param api_endpoint: Optional URL of Code Carbon API endpoint for sending
                             emissions data.
        :param api_key: API key for Code Carbon API (mandatory!).
        :param output_dir: Directory path to which the experiment details are logged,
                           defaults to current directory.
        :param output_file: Name of the output CSV file, defaults to `emissions.csv`.
        :param save_to_file: Indicates if the emission artifacts should be logged to a
                             file, defaults to True.
        :param save_to_api: Indicates if the emission artifacts should be sent to the
                            CodeCarbon API, defaults to False.
        :param save_to_logger: Indicates if the emission artifacts should be written
                            to a dedicated logger, defaults to False.
        :param logging_logger: LoggerOutput object encapsulating a logging.logger
                            or a Google Cloud logger.
        :param save_to_prometheus: Indicates if the emission artifacts should be
                            pushed to prometheus, defaults to False.
        :param save_to_logfire: Indicates if the emission artifacts should be written
                            to a logfire observability platform, defaults to False.
        :param prometheus_url: url of the prometheus server, defaults to `localhost:9091`.
        :param gpu_ids: User-specified known gpu ids to track.
                            Defaults to None, which means that all available gpus will be tracked.
                            It needs to be a list of integers or a comma-separated string.
                            Valid examples: [1, 3, 4] or "1,2".
        :param emissions_endpoint: Optional URL of http endpoint for sending emissions
                                   data.
        :param experiment_id: Id of the experiment.
        :param experiment_name: Label of the experiment
        :param co2_signal_api_token: API token for co2signal.com (requires sign-up for
                                     free beta)
        :param tracking_mode: One of "process" or "machine" in order to measure the
                              power consumption due to the entire machine or to try and
                              isolate the tracked processe's in isolation.
                              Defaults to "machine".
        :param log_level: Global codecarbon log level. Accepts one of:
                            {"debug", "info", "warning", "error", "critical"}.
                          Defaults to "info".
        :param on_csv_write: "append" or "update". Whether to always append a new line
                             to the csv when writing or to update the existing `run_id`
                             row (useful when calling`tracker.flush()` manually).
                             Accepts one of "append" or "update". Default is "append".
        :param logger_preamble: String to systematically include in the logger.
                                messages. Defaults to "".
        :param default_cpu_power: cpu power to be used as default if the cpu is not known.
        :param pue: PUE (Power Usage Effectiveness) of the datacenter.
        :param allow_multiple_runs: Allow multiple instances of codecarbon running in parallel. Defaults to False.
        """

        # logger.info("base tracker init")
        self._external_conf = get_hierarchical_config()
        self._set_from_conf(allow_multiple_runs, "allow_multiple_runs", False, bool)
        if self._allow_multiple_runs:
            logger.warning(
                "Multiple instances of codecarbon are allowed to run at the same time."
            )
        else:
            # Acquire lock file to prevent multiple instances of codecarbon running
            # at the same time
            try:
                self._lock = Lock()
                self._lock.acquire()
            except FileExistsError:
                logger.error(
                    f"Error: Another instance of codecarbon is probably running as we find `{self._lock.lockfile_path}`. Turn off the other instance to be able to run this one or use `allow_multiple_runs` or delete the file. Exiting."
                )
                # Do not continue if another instance of codecarbon is running
                self._another_instance_already_running = True
                return

        self._set_from_conf(api_call_interval, "api_call_interval", 8, int)
        self._set_from_conf(api_endpoint, "api_endpoint", "https://api.codecarbon.io")
        self._set_from_conf(api_key, "api_key", "api_key")
        self._set_from_conf(co2_signal_api_token, "co2_signal_api_token")
        self._set_from_conf(emissions_endpoint, "emissions_endpoint")
        self._set_from_conf(experiment_name, "experiment_name", "base")
        self._set_from_conf(gpu_ids, "gpu_ids")
        self._set_from_conf(log_level, "log_level", "info")
        self._set_from_conf(measure_power_secs, "measure_power_secs", 15, float)
        self._set_from_conf(output_dir, "output_dir", ".")
        self._set_from_conf(output_file, "output_file", "emissions.csv")
        self._set_from_conf(project_name, "project_name", "codecarbon")
        self._set_from_conf(save_to_api, "save_to_api", False, bool)
        self._set_from_conf(save_to_file, "save_to_file", True, bool)
        self._set_from_conf(save_to_logger, "save_to_logger", False, bool)
        self._set_from_conf(logging_logger, "logging_logger")
        self._set_from_conf(save_to_prometheus, "save_to_prometheus", False, bool)
        self._set_from_conf(save_to_logfire, "save_to_logfire", False, bool)
        self._set_from_conf(prometheus_url, "prometheus_url", "localhost:9091")
        self._set_from_conf(output_handlers, "output_handlers", [])
        self._set_from_conf(tracking_mode, "tracking_mode", "machine")
        self._set_from_conf(on_csv_write, "on_csv_write", "append")
        self._set_from_conf(logger_preamble, "logger_preamble", "")
        self._set_from_conf(default_cpu_power, "default_cpu_power")
        self._set_from_conf(pue, "pue", 1.0, float)
        self._set_from_conf(
            experiment_id, "experiment_id", "5b0fa12a-3dd7-45bb-9766-cc326314d9f1"
        )

        assert self._tracking_mode in ["machine", "process"]
        set_logger_level(self._log_level)
        set_logger_format(self._logger_preamble)

        self._start_time: Optional[float] = None
        self._last_measured_time: float = time.perf_counter()
        self._total_energy: Energy = Energy.from_energy(kWh=0)
        self._total_cpu_energy: Energy = Energy.from_energy(kWh=0)
        self._total_gpu_energy: Energy = Energy.from_energy(kWh=0)
        self._total_ram_energy: Energy = Energy.from_energy(kWh=0)
        self._cpu_power: Power = Power.from_watts(watts=0)
        self._gpu_power: Power = Power.from_watts(watts=0)
        self._ram_power: Power = Power.from_watts(watts=0)
        self._measure_occurrence: int = 0
        self._cloud = None
        self._previous_emissions = None
        self._conf["os"] = platform.platform()
        self._conf["python_version"] = platform.python_version()
        self._conf["cpu_count"] = count_cpus()
        self._geo = None
        self._task_start_measurement_values = {}
        self._task_stop_measurement_values = {}
        self._tasks: Dict[str, Task] = {}
        self._active_task: Optional[str] = None

        # Tracking mode detection
        ressource_tracker = ResourceTracker(self)
        ressource_tracker.set_CPU_GPU_ram_tracking()

        self._conf["hardware"] = list(map(lambda x: x.description(), self._hardware))

        logger.info(">>> Tracker's metadata:")
        logger.info(f"  Platform system: {self._conf.get('os')}")
        logger.info(f"  Python version: {self._conf.get('python_version')}")
        logger.info(f"  CodeCarbon version: {self._conf.get('codecarbon_version')}")
        logger.info(f"  Available RAM : {self._conf.get('ram_total_size'):.3f} GB")
        logger.info(f"  CPU count: {self._conf.get('cpu_count')}")
        logger.info(f"  CPU model: {self._conf.get('cpu_model')}")
        logger.info(f"  GPU count: {self._conf.get('gpu_count')}")
        if self._gpu_ids:
            logger.info(
                f"  GPU model: {self._conf.get('gpu_model')} BUT only tracking these GPU ids : {self._conf.get('gpu_ids')}"
            )
        else:
            logger.info(f"  GPU model: {self._conf.get('gpu_model')}")

        # Run `self._measure_power_and_energy` every `measure_power_secs` seconds in a
        # background thread
        self._scheduler = PeriodicScheduler(
            function=self._measure_power_and_energy,
            interval=self._measure_power_secs,
        )

        self._data_source = DataSource()

        cloud: CloudMetadata = self._get_cloud_metadata()

        if cloud.is_on_private_infra:
            self._geo = self._get_geo_metadata()
            self._conf["longitude"] = self._geo.longitude
            self._conf["latitude"] = self._geo.latitude
            self._conf["region"] = cloud.region
            self._conf["provider"] = cloud.provider
        else:
            self._conf["region"] = cloud.region
            self._conf["provider"] = cloud.provider

        self._emissions: Emissions = Emissions(
            self._data_source, self._co2_signal_api_token
        )
        self._init_output_methods(api_key=self._api_key)

    def _init_output_methods(self, *, api_key: str = None):
        """
        Prepare the different output methods
        """
        if self._save_to_file:
            self._output_handlers.append(
                FileOutput(
                    self._output_file,
                    self._output_dir,
                    self._on_csv_write,
                )
            )

        if self._save_to_logger:
            self._output_handlers.append(self._logging_logger)

        if self._emissions_endpoint:
            self._output_handlers.append(HTTPOutput(self._emissions_endpoint))

        if self._save_to_api:
            cc_api__out = CodeCarbonAPIOutput(
                endpoint_url=self._api_endpoint,
                experiment_id=self._experiment_id,
                api_key=api_key,
                conf=self._conf,
            )
            self.run_id = cc_api__out.run_id
            self._output_handlers.append(cc_api__out)
        else:
            self.run_id = uuid.uuid4()

        if self._save_to_prometheus:
            self._output_handlers.append(PrometheusOutput(self._prometheus_url))

        if self._save_to_logfire:
            self._output_handlers.append(LogfireOutput())

    def service_shutdown(self, signum, frame):
        logger.warning("service_shutdown - Caught signal %d" % signum)
        self.stop()

    @suppress(Exception)
    def start(self) -> None:
        """
        Starts tracking the experiment.
        Currently, Nvidia GPUs are supported.
        :return: None
        """
        # if another instance of codecarbon is already running, stop here
        if (
            hasattr(self, "_another_instance_already_running")
            and self._another_instance_already_running
        ):
            logger.warning(
                "Another instance of codecarbon is already running. Exiting."
            )
            return
        if self._start_time is not None:
            logger.warning("Already started tracking")
            return

        self._last_measured_time = self._start_time = time.perf_counter()
        # Read initial energy for hardware
        for hardware in self._hardware:
            hardware.start()

        self._scheduler.start()

    def start_task(self, task_name=None) -> None:
        """
        Start tracking a dedicated execution task.
        :param task_name: Name of the task to be isolated.
        :return: None
        """
        # Stop scheduler as we do not want it to interfere with the task measurement
        if self._scheduler:
            self._scheduler.stop()

        if self._active_task:
            logger.info("A task is already under measure")
            return
        if not task_name:
            task_name = uuid.uuid4().__str__()
        if task_name in self._tasks.keys():
            task_name += "_" + uuid.uuid4().__str__()
        self._last_measured_time = self._start_time = time.perf_counter()
        # Read initial energy for hardware
        for hardware in self._hardware:
            hardware.start()
        _ = self._prepare_emissions_data()
        _ = self._compute_emissions_delta(_)

        self._tasks.update(
            {
                task_name: Task(
                    task_name=task_name,
                )
            }
        )
        self._active_task = task_name

    def stop_task(self, task_name: str = None) -> float:
        """
        Stop tracking a dedicated execution task. Delta energy is computed by task, to isolate its contribution to total
        emissions.
        :return: None
        """
        task_name = task_name if task_name else self._active_task
        self._measure_power_and_energy()

        emissions_data = self._prepare_emissions_data()
        emissions_data_delta = self._compute_emissions_delta(emissions_data)

        task_duration = Time.from_seconds(
            time.perf_counter() - self._tasks[task_name].start_time
        )

        task_emission_data = emissions_data_delta
        task_emission_data.duration = task_duration.seconds
        self._tasks[task_name].emissions_data = task_emission_data
        self._tasks[task_name].is_active = False
        self._active_task = None
        return task_emission_data

    @suppress(Exception)
    def flush(self) -> Optional[float]:
        """
        Write the emissions to disk or call the API depending on the configuration,
        but keep running the experiment.
        :return: CO2 emissions in kgs
        """
        if self._start_time is None:
            logger.error("You first need to start the tracker.")
            return None

        # Run to calculate the power used from last
        # scheduled measurement to shutdown
        self._measure_power_and_energy()

        emissions_data = self._prepare_emissions_data()
        emissions_data_delta = self._compute_emissions_delta(emissions_data)

        self._persist_data(
            total_emissions=emissions_data, delta_emissions=emissions_data_delta
        )

        return emissions_data.emissions

    @suppress(Exception)
    def stop(self) -> Optional[float]:
        """
        Stops tracking the experiment
        :return: CO2 emissions in kgs
        """

        # if another instance of codecarbon is already running, Nothing to do here
        if (
            hasattr(self, "_another_instance_already_running")
            and self._another_instance_already_running
        ):
            logger.warning(
                "Another instance of codecarbon is already running. Exiting."
            )
            return
        if not self._allow_multiple_runs:
            # Release the lock
            self._lock.release()
        if self._start_time is None:
            logger.error("You first need to start the tracker.")
            return None

        if self._scheduler:
            self._scheduler.stop()
            self._scheduler = None
        else:
            logger.warning("Tracker already stopped !")
        for task_name in self._tasks:
            if self._tasks[task_name].is_active:
                self.stop_task(task_name=task_name)
        # Run to calculate the power used from last
        # scheduled measurement to shutdown
        # or if scheduler interval was longer than the run
        self._measure_power_and_energy()

        emissions_data = self._prepare_emissions_data()
        emissions_data_delta = self._compute_emissions_delta(emissions_data)

        self._persist_data(
            total_emissions=emissions_data,
            delta_emissions=emissions_data_delta,
            experiment_name=self._experiment_name,
        )

        self.final_emissions_data = emissions_data
        self.final_emissions = emissions_data.emissions
        return emissions_data.emissions

    def _persist_data(
        self,
        total_emissions: EmissionsData,
        delta_emissions: EmissionsData,
        experiment_name=None,
    ):
        task_emissions_data = []
        for task in self._tasks:
            task_emissions_data.append(self._tasks[task].out())

        for handler in self._output_handlers:
            handler.out(total_emissions, delta_emissions)
            if len(task_emissions_data) > 0:
                handler.task_out(task_emissions_data, experiment_name)

    def _prepare_emissions_data(self) -> EmissionsData:
        """
        :delta: If 'True', return only the delta comsumption since the last call.
        """
        cloud: CloudMetadata = self._get_cloud_metadata()
        duration: Time = Time.from_seconds(time.perf_counter() - self._start_time)

        if cloud.is_on_private_infra:
            emissions = self._emissions.get_private_infra_emissions(
                self._total_energy, self._geo
            )  # float: kg co2_eq
            country_name = self._geo.country_name
            country_iso_code = self._geo.country_iso_code
            region = self._geo.region
            on_cloud = "N"
            cloud_provider = ""
            cloud_region = ""
        else:
            emissions = self._emissions.get_cloud_emissions(
                self._total_energy, cloud, self._geo
            )
            country_name = self._emissions.get_cloud_country_name(cloud)
            country_iso_code = self._emissions.get_cloud_country_iso_code(cloud)
            region = self._emissions.get_cloud_geo_region(cloud)
            on_cloud = "Y"
            cloud_provider = cloud.provider
            cloud_region = cloud.region
        total_emissions = EmissionsData(
            timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            project_name=self._project_name,
            run_id=str(self.run_id),
            experiment_id=str(self._experiment_id),
            duration=duration.seconds,
            emissions=emissions,  # kg
            emissions_rate=emissions / duration.seconds,  # kg/s
            cpu_power=self._cpu_power.W,
            gpu_power=self._gpu_power.W,
            ram_power=self._ram_power.W,
            cpu_energy=self._total_cpu_energy.kWh,
            gpu_energy=self._total_gpu_energy.kWh,
            ram_energy=self._total_ram_energy.kWh,
            energy_consumed=self._total_energy.kWh,
            country_name=country_name,
            country_iso_code=country_iso_code,
            region=region,
            on_cloud=on_cloud,
            cloud_provider=cloud_provider,
            cloud_region=cloud_region,
            os=self._conf.get("os"),
            python_version=self._conf.get("python_version"),
            codecarbon_version=self._conf.get("codecarbon_version"),
            gpu_count=self._conf.get("gpu_count"),
            gpu_model=self._conf.get("gpu_model"),
            cpu_count=self._conf.get("cpu_count"),
            cpu_model=self._conf.get("cpu_model"),
            longitude=self._conf.get("longitude"),
            latitude=self._conf.get("latitude"),
            ram_total_size=self._conf.get("ram_total_size"),
            tracking_mode=self._conf.get("tracking_mode"),
            pue=self._pue,
        )
        logger.debug(total_emissions)
        return total_emissions

    def _compute_emissions_delta(self, total_emissions: EmissionsData) -> EmissionsData:
        delta_emissions: EmissionsData = total_emissions
        if self._previous_emissions is None:
            self._previous_emissions = total_emissions
        else:
            # Create a copy
            delta_emissions = dataclasses.replace(total_emissions)
            # Compute emissions rate from delta
            delta_emissions.compute_delta_emission(self._previous_emissions)
            # TODO : find a way to store _previous_emissions only when
            # TODO : the API call succeeded
            self._previous_emissions = total_emissions
        return delta_emissions

    @abstractmethod
    def _get_geo_metadata(self) -> GeoMetadata:
        """
        :return: Metadata containing geographical info
        """

    @abstractmethod
    def _get_cloud_metadata(self) -> CloudMetadata:
        """
        :return: Metadata containing cloud info
        """

    def _do_measurements(self) -> None:
        for hardware in self._hardware:
            h_time = time.perf_counter()
            # Compute last_duration again for more accuracy
            last_duration = time.perf_counter() - self._last_measured_time
            (
                power,
                energy,
            ) = hardware.measure_power_and_energy(last_duration=last_duration)
            # Apply the PUE of the datacenter to the consumed energy
            energy *= self._pue
            self._total_energy += energy
            if isinstance(hardware, CPU):
                self._total_cpu_energy += energy
                self._cpu_power = power
                logger.info(
                    f"Energy consumed for all CPUs : {self._total_cpu_energy.kWh:.6f} kWh"
                    + f". Total CPU Power : {self._cpu_power.W} W"
                )
            elif isinstance(hardware, GPU):
                self._total_gpu_energy += energy
                self._gpu_power = power
                logger.info(
                    f"Energy consumed for all GPUs : {self._total_gpu_energy.kWh:.6f} kWh"
                    + f". Total GPU Power : {self._gpu_power.W} W"
                )
            elif isinstance(hardware, RAM):
                self._total_ram_energy += energy
                self._ram_power = power
                logger.info(
                    f"Energy consumed for RAM : {self._total_ram_energy.kWh:.6f} kWh"
                    + f". RAM Power : {self._ram_power.W} W"
                )
            elif isinstance(hardware, AppleSiliconChip):
                if hardware.chip_part == "CPU":
                    self._total_cpu_energy += energy
                    self._cpu_power = power
                    logger.info(
                        f"Energy consumed for all CPUs : {self._total_cpu_energy.kWh:.6f} kWh"
                        + f". Total CPU Power : {self._cpu_power.W} W"
                    )
                elif hardware.chip_part == "GPU":
                    self._total_gpu_energy += energy
                    self._gpu_power = power
                    logger.info(
                        f"Energy consumed for all GPUs : {self._total_gpu_energy.kWh:.6f} kWh"
                        + f". Total GPU Power : {self._gpu_power.W} W"
                    )
            else:
                logger.error(f"Unknown hardware type: {hardware} ({type(hardware)})")
            h_time = time.perf_counter() - h_time
            logger.debug(
                f"{hardware.__class__.__name__} : {hardware.total_power().W:,.2f} "
                + f"W during {last_duration:,.2f} s [measurement time: {h_time:,.4f}]"
            )
        logger.info(
            f"{self._total_energy.kWh:.6f} kWh of electricity used since the beginning."
        )

    def _measure_power_and_energy(self) -> None:
        """
        A function that is periodically run by the `BackgroundScheduler`
        every `self._measure_power_secs` seconds.
        :return: None
        """
        last_duration = time.perf_counter() - self._last_measured_time

        warning_duration = self._measure_power_secs * 3
        if last_duration > warning_duration:
            warn_msg = (
                "Background scheduler didn't run for a long period"
                + " (%ds), results might be inaccurate"
            )
            logger.warning(warn_msg, last_duration)

        self._do_measurements()
        self._last_measured_time = time.perf_counter()
        self._measure_occurrence += 1
        # Special case: metrics and api calls are sent every `api_call_interval` measures
        if (
            self._api_call_interval != -1
            and len(self._output_handlers) > 0
            and self._measure_occurrence >= self._api_call_interval
        ):
            emissions = self._prepare_emissions_data()
            emissions_delta = self._compute_emissions_delta(emissions)
            logger.info(
                f"{emissions_delta.emissions_rate * 1000:.6f} g.CO2eq/s mean an estimation of "
                + f"{emissions_delta.emissions_rate * 3600 * 24 * 365:,} kg.CO2eq/year"
            )
            for handler in self._output_handlers:
                handler.live_out(emissions, emissions_delta)
            self._measure_occurrence = 0
        logger.debug(f"last_duration={last_duration}\n------------------------")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, tb) -> None:
        self.stop()


class OfflineEmissionsTracker(BaseEmissionsTracker):
    """
    Offline implementation of the `EmissionsTracker`
    In addition to the standard arguments, the following are required.
    """

    @suppress(Exception)
    def __init__(
        self,
        *args,
        country_iso_code: Optional[str] = _sentinel,
        region: Optional[str] = _sentinel,
        cloud_provider: Optional[str] = _sentinel,
        cloud_region: Optional[str] = _sentinel,
        country_2letter_iso_code: Optional[str] = _sentinel,
        **kwargs,
    ):
        """
        :param country_iso_code: 3 letter ISO Code of the country where the
                                 experiment is being run
        :param region: The province or region (e.g. California in the US).
                       Currently, this only affects calculations for the United States
                       and Canada
        :param cloud_provider: The cloud provider specified for estimating emissions
                               intensity, defaults to None.
                               See https://github.com/mlco2/codecarbon/
                                        blob/master/codecarbon/data/cloud/impact.csv
                               for a list of cloud providers
        :param cloud_region: The region of the cloud data center, defaults to None.
                             See https://github.com/mlco2/codecarbon/
                                        blob/master/codecarbon/data/cloud/impact.csv
                             for a list of cloud regions.
        :param country_2letter_iso_code: For use with the CO2Signal emissions API.
                                         See http://api.electricitymap.org/v3/zones for
                                         a list of codes and their corresponding
                                         locations.
        """
        self._external_conf = get_hierarchical_config()
        self._set_from_conf(cloud_provider, "cloud_provider")
        self._set_from_conf(cloud_region, "cloud_region")
        self._set_from_conf(country_2letter_iso_code, "country_2letter_iso_code")
        self._set_from_conf(country_iso_code, "country_iso_code")
        self._set_from_conf(region, "region")

        logger.info("offline tracker init")

        if self._region is not None:
            assert isinstance(self._region, str)
            self._region: str = self._region.lower()

        if self._cloud_provider:
            if self._cloud_region is None:
                logger.error(
                    "Cloud Region must be provided " + " if cloud provider is set"
                )

            df = DataSource().get_cloud_emissions_data()
            if (
                len(
                    df.loc[
                        (df["provider"] == self._cloud_provider)
                        & (df["region"] == self._cloud_region)
                    ]
                )
                == 0
            ):
                logger.error(
                    "Cloud Provider/Region "
                    f"{self._cloud_provider} {self._cloud_region} "
                    "not found in cloud emissions data."
                )
        if self._country_iso_code:
            try:
                self._country_name: str = DataSource().get_global_energy_mix_data()[
                    self._country_iso_code
                ]["country_name"]
            except KeyError as e:
                logger.error(
                    "Does not support country"
                    + f" with ISO code {self._country_iso_code} "
                    f"Exception occurred {e}"
                )

        if self._country_2letter_iso_code:
            assert isinstance(self._country_2letter_iso_code, str)
            self._country_2letter_iso_code: str = self._country_2letter_iso_code.upper()

        super().__init__(*args, **kwargs)

    def _get_geo_metadata(self) -> GeoMetadata:
        return GeoMetadata(
            country_iso_code=self._country_iso_code,
            country_name=self._country_name,
            region=self._region,
            country_2letter_iso_code=self._country_2letter_iso_code,
        )

    def _get_cloud_metadata(self) -> CloudMetadata:
        if self._cloud is None:
            self._cloud = CloudMetadata(
                provider=self._cloud_provider, region=self._cloud_region
            )
        return self._cloud


class EmissionsTracker(BaseEmissionsTracker):
    """
    An online emissions tracker that auto infers geographical location,
    using the `geojs` API
    """

    def _get_geo_metadata(self) -> GeoMetadata:
        return GeoMetadata.from_geo_js(self._data_source.geo_js_url)

    def _get_cloud_metadata(self) -> CloudMetadata:
        if self._cloud is None:
            self._cloud = CloudMetadata.from_utils()
        return self._cloud


class TaskEmissionsTracker:
    """
    Track emissions for a specific task
    # TODO: THIS NOT USED, RIGHT ?
    """

    def __init__(self, task_name, tracker: EmissionsTracker = None):
        self.is_default_tracker = False
        if tracker:
            self.tracker = tracker
        else:
            self.tracker = EmissionsTracker()
            self.is_default_tracker = True
        self.task_name = task_name

    def __enter__(self):
        self.tracker.start_task(self.task_name)
        return self

    def __exit__(self, exc_type, exc_value, tb) -> None:
        self.tracker.stop_task()
        if self.is_default_tracker:
            self.tracker.stop()


def track_emissions(
    fn: Callable = None,
    project_name: Optional[str] = _sentinel,
    measure_power_secs: Optional[int] = _sentinel,
    api_call_interval: int = _sentinel,
    api_endpoint: Optional[str] = _sentinel,
    api_key: Optional[str] = _sentinel,
    output_dir: Optional[str] = _sentinel,
    output_file: Optional[str] = _sentinel,
    save_to_file: Optional[bool] = _sentinel,
    save_to_api: Optional[bool] = _sentinel,
    save_to_logger: Optional[bool] = _sentinel,
    logging_logger: Optional[LoggerOutput] = _sentinel,
    save_to_prometheus: Optional[bool] = _sentinel,
    save_to_logfire: Optional[bool] = _sentinel,
    prometheus_url: Optional[str] = _sentinel,
    output_handlers: Optional[List[BaseOutput]] = _sentinel,
    gpu_ids: Optional[List] = _sentinel,
    emissions_endpoint: Optional[str] = _sentinel,
    experiment_id: Optional[str] = _sentinel,
    experiment_name: Optional[str] = _sentinel,
    co2_signal_api_token: Optional[str] = _sentinel,
    tracking_mode: Optional[str] = _sentinel,
    log_level: Optional[Union[int, str]] = _sentinel,
    on_csv_write: Optional[str] = _sentinel,
    logger_preamble: Optional[str] = _sentinel,
    default_cpu_power: Optional[int] = _sentinel,
    pue: Optional[int] = _sentinel,
    allow_multiple_runs: Optional[bool] = _sentinel,
    offline: Optional[bool] = _sentinel,
    country_iso_code: Optional[str] = _sentinel,
    region: Optional[str] = _sentinel,
    cloud_provider: Optional[str] = _sentinel,
    cloud_region: Optional[str] = _sentinel,
    country_2letter_iso_code: Optional[str] = _sentinel,
):
    """
    Decorator that supports both `EmissionsTracker` and `OfflineEmissionsTracker`
    :param fn: Function to be decorated
    :param project_name: Project name for current experiment run,
                         default name is "codecarbon".
    :param measure_power_secs: Interval (in seconds) to measure hardware power usage,
                               defaults to 15.
    :param api_call_interval: Number of measure to make before calling the Code Carbon API.
    :param api_endpoint: Optional URL of Code Carbon API endpoint for sending
                         emissions data.
    :param api_key: API key for Code Carbon API (mandatory!).
    :param output_dir: Directory path to which the experiment details are logged,
                       defaults to current directory.
    :param output_file: Name of output CSV file, defaults to `emissions.csv`
    :param save_to_file: Indicates if the emission artifacts should be logged to a file,
                         defaults to True.
    :param save_to_api: Indicates if the emission artifacts should be send to the
                        CodeCarbon API, defaults to False.
    :param save_to_logger: Indicates if the emission artifacts should be written
                        to a dedicated logger, defaults to False.
    :param logging_logger: LoggerOutput object encapsulating a logging.logger
                        or a Google Cloud logger.
    :param save_to_prometheus: Indicates if the emission artifacts should be
                            pushed to prometheus, defaults to False.
    :param save_to_logfire: Indicates if the emission artifacts should be
                            pushed to logfire, defaults to False.
    :param prometheus_url: url of the prometheus server, defaults to `localhost:9091`.
    :param output_handlers: List of output handlers to use.
    :param gpu_ids: User-specified known gpu ids to track.
                    Defaults to None, which means that all available gpus will be tracked.
                    It needs to be a list of integers or a comma-separated string.
                    Valid examples: [1, 3, 4] or "1,2".
    :param emissions_endpoint: Optional URL of http endpoint for sending emissions
                               data.
    :param experiment_id: Id of the experiment.
    :param experiment_name: Label of the experiment
    :param co2_signal_api_token: API token for co2signal.com (requires sign-up for
                                 free beta)
    :param tracking_mode: One of "process" or "machine" in order to measure the
                          power consumption due to the entire machine or to try and
                          isolate the tracked processe's in isolation.
                          Defaults to "machine".
    :param log_level: Global codecarbon log level. Accepts one of:
                      {"debug", "info", "warning", "error", "critical"}.
                      Defaults to "info".
    :param on_csv_write: "append" or "update". Whether to always append a new line
                         to the csv when writing or to update the existing `run_id`
                         row (useful when calling`tracker.flush()` manually).
                         Accepts one of "append" or "update". Default is "append".
    :param logger_preamble: String to systematically include in the logger.
                            messages. Defaults to "".
    :param default_cpu_power: cpu power to be used as default if the cpu is not known.
    :param pue: PUE (Power Usage Effectiveness) of the datacenter.
    :param allow_multiple_runs: Prevent multiple instances of codecarbon running. Defaults to False.
    :param offline: Indicates if the tracker should be run in offline mode.
    :param country_iso_code: 3 letter ISO Code of the country where the experiment is
                             being run, required if `offline=True`
    :param region: The provice or region (e.g. California in the US).
                   Currently, this only affects calculations for the United States.
    :param cloud_provider: The cloud provider specified for estimating emissions
                           intensity, defaults to None.
                           See https://github.com/mlco2/codecarbon/
                                            blob/master/codecarbon/data/cloud/impact.csv
                           for a list of cloud providers.
    :param cloud_region: The region of the cloud data center, defaults to None.
                         See https://github.com/mlco2/codecarbon/
                                            blob/master/codecarbon/data/cloud/impact.csv
                         for a list of cloud regions.
    :param country_2letter_iso_code: For use with the CO2Signal emissions API.
                                     See http://api.electricitymap.org/v3/zones for
                                     a list of codes and their corresponding
                                     locations.

    :return: The decorated function
    """

    def _decorate(fn: Callable):
        @wraps(fn)
        def wrapped_fn(*args, **kwargs):
            fn_result = None
            if offline and offline is not _sentinel:
                if (country_iso_code is None or country_iso_code is _sentinel) and (
                    cloud_provider is None or cloud_provider is _sentinel
                ):
                    raise Exception("Needs ISO Code of the Country for Offline mode")
                tracker = OfflineEmissionsTracker(
                    project_name=project_name,
                    measure_power_secs=measure_power_secs,
                    output_dir=output_dir,
                    output_file=output_file,
                    save_to_file=save_to_file,
                    save_to_logger=save_to_logger,
                    logging_logger=logging_logger,
                    save_to_prometheus=save_to_prometheus,
                    save_to_logfire=save_to_logfire,
                    prometheus_url=prometheus_url,
                    output_handlers=output_handlers,
                    gpu_ids=gpu_ids,
                    experiment_id=experiment_id,
                    co2_signal_api_token=co2_signal_api_token,
                    tracking_mode=tracking_mode,
                    log_level=log_level,
                    on_csv_write=on_csv_write,
                    logger_preamble=logger_preamble,
                    default_cpu_power=default_cpu_power,
                    pue=pue,
                    allow_multiple_runs=allow_multiple_runs,
                    country_iso_code=country_iso_code,
                    region=region,
                    cloud_provider=cloud_provider,
                    cloud_region=cloud_region,
                    country_2letter_iso_code=country_2letter_iso_code,
                )
            else:
                tracker = EmissionsTracker(
                    project_name=project_name,
                    measure_power_secs=measure_power_secs,
                    api_call_interval=api_call_interval,
                    api_endpoint=api_endpoint,
                    api_key=api_key,
                    output_dir=output_dir,
                    output_file=output_file,
                    save_to_file=save_to_file,
                    save_to_api=save_to_api,
                    save_to_logger=save_to_logger,
                    logging_logger=logging_logger,
                    save_to_prometheus=save_to_prometheus,
                    save_to_logfire=save_to_logfire,
                    prometheus_url=prometheus_url,
                    output_handlers=output_handlers,
                    gpu_ids=gpu_ids,
                    emissions_endpoint=emissions_endpoint,
                    experiment_id=experiment_id,
                    experiment_name=experiment_name,
                    co2_signal_api_token=co2_signal_api_token,
                    tracking_mode=tracking_mode,
                    log_level=log_level,
                    on_csv_write=on_csv_write,
                    logger_preamble=logger_preamble,
                    default_cpu_power=default_cpu_power,
                    pue=pue,
                    allow_multiple_runs=allow_multiple_runs,
                )
            tracker.start()
            try:
                fn_result = fn(*args, **kwargs)
            finally:
                logger.info(
                    "\nGraceful stopping: collecting and writing information.\n"
                    + "Please wait a few seconds..."
                )
                tracker.stop()
                logger.info("Done!\n")
            return fn_result

        return wrapped_fn

    if fn:
        return _decorate(fn)
    return _decorate


def track_task_emissions(
    fn: Callable = None, tracker: BaseEmissionsTracker = None, task_name: str = ""
):
    """
    Decorator to track emissions specific to a task. With a tracker as input, it will add task emissions to global emissions.
    :param: tracker: global tracker used in the current execution. If none is provided, instanciates an emission
    tracker which will read default parameter from config to enable tracking
    :param: task_name: Task to be tracked. If none is provided, an id will be used.
    :return: The decorated function
    """

    if not tracker:
        is_tracker_default = True
        tracker = EmissionsTracker()
    else:
        is_tracker_default = False

    def _decorate(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapped_fn(*args, **kwargs):
            fn_result = None
            tracker.start_task(task_name=task_name)
            try:
                fn_result = fn(*args, **kwargs)
            finally:
                logger.info(
                    "\nGraceful stopping task measurement: collecting and writing information.\n"
                    + "Please Allow for a few seconds..."
                )
                tracker.stop_task()
                if is_tracker_default:
                    tracker.stop()
                logger.info("Done!\n")
            return fn_result

        return wrapped_fn

    if fn:
        return _decorate(fn)
    return _decorate
