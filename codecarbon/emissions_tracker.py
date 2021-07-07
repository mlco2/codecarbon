"""
Contains implementations of the Public facing API: EmissionsTracker,
OfflineEmissionsTracker and @track_emissions
"""
import dataclasses
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from functools import wraps
from typing import Callable, List, Optional, Union

from apscheduler.schedulers.background import BackgroundScheduler

from codecarbon.core import cpu, gpu
from codecarbon.core.config import get_hierarchical_config, parse_gpu_ids
from codecarbon.core.emissions import Emissions
from codecarbon.core.units import Energy, Time
from codecarbon.core.util import set_log_level, suppress
from codecarbon.external.geography import CloudMetadata, GeoMetadata
from codecarbon.external.hardware import CPU, GPU, RAM
from codecarbon.external.logger import logger
from codecarbon.input import DataSource
from codecarbon.output import (
    BaseOutput,
    CodeCarbonAPIOutput,
    EmissionsData,
    FileOutput,
    HTTPOutput,
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
    that are implemented by two concrete classes `OfflineCarbonTracker`
    and `CarbonTracker.`
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
            self._conf = {}

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
        measure_power_secs: Optional[int] = _sentinel,
        api_call_interval: Optional[int] = _sentinel,
        api_endpoint: Optional[str] = _sentinel,
        api_key: Optional[str] = _sentinel,
        output_dir: Optional[str] = _sentinel,
        save_to_file: Optional[bool] = _sentinel,
        save_to_api: Optional[bool] = _sentinel,
        gpu_ids: Optional[List] = _sentinel,
        emissions_endpoint: Optional[str] = _sentinel,
        experiment_id: Optional[str] = _sentinel,
        co2_signal_api_token: Optional[str] = _sentinel,
        tracking_mode: Optional[str] = _sentinel,
        log_level: Optional[Union[int, str]] = _sentinel,
    ):
        """
        :param project_name: Project name for current experiment run, default name
                             as "codecarbon"
        :param measure_power_secs: Interval (in seconds) to measure hardware power
                                   usage, defaults to 15
        :param api_call_interval: Occurence to wait before calling API :
                            1 : at every measure
                            2 : every 2 measure, etc...
        :param api_endpoint: Optional URL of Code Carbon API endpoint for sending
                             emissions data
        :param api_key: API key for Code Carbon API, mandatory to use it !
        :param output_dir: Directory path to which the experiment details are logged
                           in a CSV file called `emissions.csv`, defaults to current
                           directory
        :param save_to_file: Indicates if the emission artifacts should be logged to a
                             file, defaults to True
        :param save_to_api: Indicates if the emission artifacts should be send to the
                            CodeCarbon API, defaults to False
        :param gpu_ids: User-specified known gpu ids to track, defaults to None
        :param emissions_endpoint: Optional URL of http endpoint for sending emissions
                                   data
        :param experiment_id: Id of the experiment
        :param co2_signal_api_token: API token for co2signal.com (requires sign-up for
                                     free beta)
        :param tracking_mode: One of "process" or "machine" in order to measure the
                              power consumptions due to the entire machine or try and
                              isolate the tracked processe's in isolation.
                              Defaults to "machine"
        :param log_level: Global codecarbon log level. Accepts one of:
                            {"debug", "info", "warning", "error", "critical"}.
                          Defaults to "info".
        """
        self._external_conf = get_hierarchical_config()

        self._set_from_conf(api_call_interval, "api_call_interval", 8, int)
        self._set_from_conf(api_endpoint, "api_endpoint", "https://api.codecarbon.io")
        self._set_from_conf(co2_signal_api_token, "co2_signal_api_token")
        self._set_from_conf(emissions_endpoint, "emissions_endpoint")
        self._set_from_conf(gpu_ids, "gpu_ids")
        self._set_from_conf(log_level, "log_level", "info")
        self._set_from_conf(measure_power_secs, "measure_power_secs", 15, int)
        self._set_from_conf(output_dir, "output_dir", ".")
        self._set_from_conf(project_name, "project_name", "codecarbon")
        self._set_from_conf(save_to_api, "save_to_api", False, bool)
        self._set_from_conf(save_to_file, "save_to_file", True, bool)
        self._set_from_conf(tracking_mode, "tracking_mode", "machine")

        assert self._tracking_mode in ["machine", "process"]
        set_log_level(self._log_level)

        self._start_time: Optional[float] = None
        self._last_measured_time: float = time.time()
        self._total_energy: Energy = Energy.from_energy(kwh=0)
        self._total_cpu_power: Energy = Energy.from_energy(kwh=0)
        self._total_gpu_power: Energy = Energy.from_energy(kwh=0)
        self._scheduler = BackgroundScheduler()
        self._hardware = [RAM(self._tracking_mode)]
        self._conf["hardware"] = []
        self._cc_api__out = None
        self._measure_occurrence: int = 0
        self._cloud = None
        self._previous_emissions = None

        if isinstance(self._gpu_ids, str):
            self._gpu_ids = parse_gpu_ids(self._gpu_ids)
            self._conf["gpu_ids"] = self._gpu_ids

        # Hardware detection
        if gpu.is_gpu_details_available():
            logger.info("Tracking Nvidia GPU via pynvml")
            self._hardware.append(GPU.from_utils(self._gpu_ids))

        if cpu.is_powergadget_available():
            logger.info("Tracking Intel CPU via Power Gadget")
            self._hardware.append(
                CPU.from_utils(self._output_dir, "intel_power_gadget")
            )
        elif cpu.is_rapl_available():
            logger.info("Tracking Intel CPU via RAPL interface")
            self._hardware.append(CPU.from_utils(self._output_dir, "intel_rapl"))
        else:
            logger.warning(
                "No CPU tracking mode found. Falling back on CPU constant mode."
            )
            logger.info("Tracking using constant")
            tdp = cpu.TDP()
            power = tdp.tdp
            model = tdp.model
            if tdp:
                self._hardware.append(
                    CPU.from_utils(self._output_dir, "constant", model, power)
                )
            else:
                logger.warning(
                    "Failed to match CPU TDP constant. "
                    + "Falling back on a global constant."
                )
                self._hardware.append(CPU.from_utils(self._output_dir, "constant"))

        self._conf["hardware"] = list(map(lambda x: x.description(), self._hardware))

        # Run `self._measure_power` every `measure_power_secs` seconds in a
        # background thread
        self._scheduler.add_job(
            self._measure_power,
            "interval",
            seconds=self._measure_power_secs,
            max_instances=1,
        )

        self._data_source = DataSource()
        self._emissions: Emissions = Emissions(
            self._data_source, self._co2_signal_api_token
        )
        self.persistence_objs: List[BaseOutput] = list()

        if self._save_to_file:
            self.persistence_objs.append(
                FileOutput(os.path.join(self._output_dir, "emissions.csv"))
            )

        if self._emissions_endpoint:
            self.persistence_objs.append(HTTPOutput(emissions_endpoint))

        if self._save_to_api:
            experiment_id = self._get_conf(
                experiment_id, "experiment_id", "5b0fa12a-3dd7-45bb-9766-cc326314d9f1"
            )
            self._cc_api__out = CodeCarbonAPIOutput(
                endpoint_url=self._api_endpoint,
                experiment_id=experiment_id,
                api_key=api_key,
            )
            self.persistence_objs.append(self._cc_api__out)

    @suppress(Exception)
    def start(self) -> None:
        """
        Starts tracking the experiment.
        Currently, Nvidia GPUs are supported.
        :return: None
        """
        if self._start_time is not None:
            logger.warning("Already started tracking")
            return

        self._last_measured_time = self._start_time = time.time()
        self._scheduler.start()

    @suppress(Exception)
    def stop(self) -> Optional[float]:
        """
        Stops tracking the experiment
        :return: CO2 emissions in kgs
        """
        if self._start_time is None:
            logger.error("Need to first start the tracker")
            return None

        self._scheduler.shutdown()

        # Run to calculate the power used from last
        # scheduled measurement to shutdown
        self._measure_power()

        emissions_data = self._prepare_emissions_data()

        for persistence in self.persistence_objs:
            if isinstance(persistence, CodeCarbonAPIOutput):
                emissions_data = self._prepare_emissions_data(delta=True)

            persistence.out(emissions_data)

        self.final_emissions = emissions_data.emissions
        return emissions_data.emissions

    def _prepare_emissions_data(self, delta=False) -> EmissionsData:
        """
        :delta: True to return only the delta comsumption since last call
        """
        cloud: CloudMetadata = self._get_cloud_metadata()
        duration: Time = Time.from_seconds(time.time() - self._start_time)

        if cloud.is_on_private_infra:
            geo: GeoMetadata = self._get_geo_metadata()
            emissions = self._emissions.get_private_infra_emissions(
                self._total_energy, geo
            )
            country_name = geo.country_name
            country_iso_code = geo.country_iso_code
            region = geo.region
            on_cloud = "N"
            cloud_provider = ""
            cloud_region = ""
        else:
            emissions = self._emissions.get_cloud_emissions(self._total_energy, cloud)
            country_name = self._emissions.get_cloud_country_name(cloud)
            country_iso_code = self._emissions.get_cloud_country_iso_code(cloud)
            region = self._emissions.get_cloud_geo_region(cloud)
            on_cloud = "Y"
            cloud_provider = cloud.provider
            cloud_region = cloud.region
        logger.debug(f"emissions={emissions}")
        total_emissions = EmissionsData(
            timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            project_name=self._project_name,
            duration=duration.seconds,
            emissions=emissions,
            cpu_power=self._total_cpu_power.kwh,
            gpu_power=self._total_gpu_power.kwh,
            energy_consumed=self._total_energy.kwh,
            country_name=country_name,
            country_iso_code=country_iso_code,
            region=region,
            on_cloud=on_cloud,
            cloud_provider=cloud_provider,
            cloud_region=cloud_region,
        )
        if delta:
            if self._previous_emissions is None:
                self._previous_emissions = total_emissions
                return total_emissions
            else:
                # Create a copy
                delta_emissions = dataclasses.replace(total_emissions)
                # Compute delta
                delta_emissions.substract_in_place(self._previous_emissions)
                # TODO : find a way to store _previous_emissions only when
                # TODO : the API call succeded
                self._previous_emissions = total_emissions
                return delta_emissions
        else:
            return total_emissions

    @abstractmethod
    def _get_geo_metadata(self) -> GeoMetadata:
        """
        :return: Metadata containing geographical info
        """
        pass

    @abstractmethod
    def _get_cloud_metadata(self) -> CloudMetadata:
        """
        :return: Metadata containing cloud info
        """
        pass

    def _measure_power(self) -> None:
        """
        A function that is periodically run by the `BackgroundScheduler`
        every `self._measure_power` seconds.
        :return: None
        """
        last_duration = time.time() - self._last_measured_time

        warning_duration = self._measure_power_secs * 3
        if last_duration > warning_duration:
            warn_msg = (
                "Background scheduler didn't run for a long period"
                + " (%ds), results might be inaccurate"
            )
            logger.warning(warn_msg, last_duration)

        for hardware in self._hardware:
            energy = Energy.from_power_and_time(
                power=hardware.total_power(), time=Time.from_seconds(last_duration)
            )
            self._total_energy += energy
            if isinstance(hardware, CPU):
                self._total_cpu_power += energy
            if isinstance(hardware, GPU):
                self._total_gpu_power += energy
            logger.info(
                "Energy consumed for all "
                + f"{hardware.__class__.__name__} : {self._total_energy.kwh:.6f} kWh"
            )
            logger.debug(
                f"\n={hardware.total_power()} power x {Time.from_seconds(last_duration)}"
            )
        self._last_measured_time = time.time()
        self._measure_occurrence += 1
        if self._cc_api__out is not None:
            if self._measure_occurrence >= self._api_call_interval:
                self._cc_api__out.out(self._prepare_emissions_data(delta=True))
                self._measure_occurrence = 0

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
        :param region: The provincial region, for example, California in the US.
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

        if self._region is not None:
            assert isinstance(self._region, str)
            self._region = self._region.lower()

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
                ]["countryName"]
            except KeyError as e:
                logger.error(
                    "Does not support country"
                    + f" with ISO code {self._country_iso_code} "
                    f"Exception occurred {e}"
                )

        if self._country_2letter_iso_code:
            assert isinstance(self._country_2letter_iso_code, str)
            self._country_2letter_iso_code = self._country_2letter_iso_code.upper()

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
    using `geojs` API
    """

    def _get_geo_metadata(self) -> GeoMetadata:
        return GeoMetadata.from_geo_js(self._data_source.geo_js_url)

    def _get_cloud_metadata(self) -> CloudMetadata:
        if self._cloud is None:
            self._cloud = CloudMetadata.from_utils()
        return self._cloud


def track_emissions(
    fn: Callable = None,
    project_name: Optional[str] = _sentinel,
    measure_power_secs: Optional[int] = _sentinel,
    api_call_interval: int = 2,
    api_endpoint: Optional[str] = _sentinel,
    api_key: Optional[str] = _sentinel,
    output_dir: Optional[str] = _sentinel,
    save_to_file: Optional[bool] = _sentinel,
    save_to_api: Optional[bool] = _sentinel,
    offline: Optional[bool] = _sentinel,
    emissions_endpoint: Optional[str] = _sentinel,
    experiment_id: Optional[str] = _sentinel,
    country_iso_code: Optional[str] = _sentinel,
    region: Optional[str] = _sentinel,
    cloud_provider: Optional[str] = _sentinel,
    cloud_region: Optional[str] = _sentinel,
    gpu_ids: Optional[List] = _sentinel,
    co2_signal_api_token: Optional[str] = _sentinel,
    log_level: Optional[Union[int, str]] = _sentinel,
):
    """
    Decorator that supports both `EmissionsTracker` and `OfflineEmissionsTracker`
    :param fn: Function to be decorated
    :param project_name: Project name for current experiment run,
                         default name as "codecarbon"
    :param measure_power_secs: Interval (in seconds) to measure hardware power usage,
                               defaults to 15
    :api_call_interval: Number of measure to make before calling the Code Carbon API.
    :param output_dir: Directory path to which the experiment details are logged
                       in a CSV file called `emissions.csv`, defaults to current
                       directory
    :param save_to_file: Indicates if the emission artifacts should be logged to a file,
                         defaults to True
    :param save_to_api: Indicates if the emission artifacts should be send to the CodeCarbon API, defaults to False
    :param offline: Indicates if the tracker should be run in offline mode
    :param country_iso_code: 3 letter ISO Code of the country where the experiment is
                             being run, required if `offline=True`
    :param region: The provincial region, for example, California in the US.
                   Currently, this only affects calculations for the United States
    :param cloud_provider: The cloud provider specified for estimating emissions
                           intensity, defaults to None.
                           See https://github.com/mlco2/codecarbon/
                                            blob/master/codecarbon/data/cloud/impact.csv
                           for a list of cloud providers
    :param cloud_region: The region of the cloud data center, defaults to None.
                         See https://github.com/mlco2/codecarbon/
                                            blob/master/codecarbon/data/cloud/impact.csv
                         for a list of cloud regions
    :param gpu_ids: User-specified known gpu ids to track, defaults to None
    :param log_level: Global codecarbon log level. Accepts one of:
                        {"debug", "info", "warning", "error", "critical"}.
                      Defaults to "info".

    :return: The decorated function
    """

    def _decorate(fn: Callable):
        @wraps(fn)
        def wrapped_fn(*args, **kwargs):
            if offline and offline is not _sentinel:
                if (country_iso_code is None or country_iso_code is _sentinel) and (
                    cloud_provider is None or cloud_provider is _sentinel
                ):
                    raise Exception("Needs ISO Code of the Country for Offline mode")
                tracker = OfflineEmissionsTracker(
                    project_name=project_name,
                    measure_power_secs=measure_power_secs,
                    output_dir=output_dir,
                    save_to_file=save_to_file,
                    country_iso_code=country_iso_code,
                    region=region,
                    cloud_provider=cloud_provider,
                    cloud_region=cloud_region,
                    gpu_ids=gpu_ids,
                    log_level=log_level,
                    co2_signal_api_token=co2_signal_api_token,
                )
                tracker.start()
                fn(*args, **kwargs)
                tracker.stop()
            else:
                tracker = EmissionsTracker(
                    project_name=project_name,
                    measure_power_secs=measure_power_secs,
                    output_dir=output_dir,
                    save_to_file=save_to_file,
                    gpu_ids=gpu_ids,
                    log_level=log_level,
                    emissions_endpoint=emissions_endpoint,
                    experiment_id=experiment_id,
                    api_call_interval=api_call_interval,
                    api_key=api_key,
                    api_endpoint=api_endpoint,
                    save_to_api=save_to_api,
                    co2_signal_api_token=co2_signal_api_token,
                )
                tracker.start()
                try:
                    fn(*args, **kwargs)
                finally:
                    logger.info(
                        "\nGraceful stopping: collecting and writing information.\n"
                        + "Please Allow for a few seconds..."
                    )
                    tracker.stop()
                    logger.info("Done!\n")

        return wrapped_fn

    if fn:
        return _decorate(fn)
    return _decorate
