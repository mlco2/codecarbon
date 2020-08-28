"""
Contains implementations of the Public facing API: CO2Tracker, OfflineCO2Tracker and @track_co2
"""

from abc import abstractmethod, ABC
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from functools import wraps
import logging
import os
import time
from typing import Optional, List, Callable
import uuid

from codecarbon.input import DataSource
from codecarbon.emissions import Emissions
from codecarbon.external.geography import GeoMetadata, CloudMetadata
from codecarbon.external.hardware import GPU
from codecarbon.output import FileOutput, CO2Data, BaseOutput
from codecarbon.units import Time, Energy
from codecarbon.utils.gpu import is_gpu_details_available

logger = logging.getLogger(__name__)


class BaseCarbonTracker(ABC):
    """
    Primary abstraction with Carbon Tracking functionality.
    Has two abstract methods, `_get_geo_metadata` and `_get_cloud_metadata`
    that are implemented by two concrete classes `OfflineCarbonTracker` and `CarbonTracker.`
    """

    def __init__(
        self,
        project_name: str = "codecarbon",
        measure_power_secs: int = 15,
        output_dir: str = ".",
        save_to_file: bool = True,
    ):
        """
        :param project_name: Project name for current experiment run, default name as "codecarbon"
        :param measure_power_secs: Interval (in seconds) to measure hardware power usage, defaults to 15
        :param output_dir: Directory path to which the experiment details are logged
                           in a CSV file called `emissions.csv`, defaults to current directory
        :param save_to_file: Indicates if the emission artifacts should be logged to a file, defaults to True
        """
        self._project_name: str = project_name
        self._measure_power_secs: int = measure_power_secs
        self._start_time: Optional[float] = None
        self._output_dir: str = output_dir
        self._total_energy: Energy = Energy.from_energy(kwh=0)
        self._scheduler = BackgroundScheduler()
        self._is_gpu_available = is_gpu_details_available()
        self._hardware = GPU.from_utils()  # TODO: Change once CPU support is available

        # Run `self._measure_power` every `measure_power_secs` seconds in a background thread:
        self._scheduler.add_job(
            self._measure_power, "interval", seconds=measure_power_secs
        )

        self._data_source = DataSource()
        self._emissions: Emissions = Emissions(self._data_source)
        self.persistence_objs: List[BaseOutput] = list()

        if save_to_file:
            self.persistence_objs.append(
                FileOutput(os.path.join(output_dir, "emissions.csv"))
            )

    def start(self) -> None:
        """
        Starts tracking the experiment.
        Currently, Nvidia GPUs are supported.
        :return: None
        """

        if self._start_time is not None:
            logger.warning("Already started tracking")
            return

        self._start_time = time.time()
        self._scheduler.start()

    def stop(self) -> Optional[float]:
        """
        Stops tracking the experiment
        :return: CO2 emissions in kgs
        """
        if self._start_time is None:
            logging.error("Need to first start the tracker")
            return None

        self._scheduler.shutdown()

        cloud: CloudMetadata = self._get_cloud_metadata()
        geo: GeoMetadata = self._get_geo_metadata()
        duration: Time = Time.from_seconds(time.time() - self._start_time)

        if cloud.is_on_private_infra:
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

        data = CO2Data(
            experiment_id=str(uuid.uuid4()),
            timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            project_name=self._project_name,
            duration=duration.seconds,
            emissions=emissions,
            energy_consumed=self._total_energy.kwh,
            country_name=country_name,
            country_iso_code=country_iso_code,
            region=region,
            on_cloud=on_cloud,
            cloud_provider=cloud_provider,
            cloud_region=cloud_region,
        )

        for persistence in self.persistence_objs:
            persistence.out(data)

        return emissions

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
        self._total_energy += Energy.from_power_and_time(
            power=self._hardware.total_power,
            time=Time.from_seconds(self._measure_power_secs),
        )


class OfflineCarbonTracker(BaseCarbonTracker):
    """
    Offline implementation of the `CarbonTracker.`
    In addition to the standard arguments, the following are required.
    """

    def __init__(
        self,
        country_iso_code: str,
        country_name: str,
        *args,
        region: Optional[str] = None,
        **kwargs
    ):
        """
        :param country_iso_code: 3 letter ISO Code of the country where the experiment is being run
        :param country_name: Name of the country where the experiment is being run
        :param region: The provincial region, for example, California in the US.
                       Currently, this only affects calculations for the United States
        """
        # TODO: Currently we silently use a default value of Canada. Decide if we should fail with missing args.
        self._country_iso_code: str = "CAN" if country_iso_code is None else country_iso_code
        self._country_name: str = "Canada" if country_name is None else country_name
        self._region: Optional[str] = region if region is None else region.lower()
        super().__init__(*args, **kwargs)

    def _get_geo_metadata(self) -> GeoMetadata:
        return GeoMetadata(
            country_iso_code=self._country_iso_code,
            country_name=self._country_name,
            region=self._region,
        )

    def _get_cloud_metadata(self) -> CloudMetadata:
        return CloudMetadata(provider=None, region=None)


class CarbonTracker(BaseCarbonTracker):
    """
    A CO2 tracker that auto infers geographical location.
    """

    def _get_geo_metadata(self) -> GeoMetadata:
        return GeoMetadata.from_geo_js(self._data_source.geo_js_url)

    def _get_cloud_metadata(self) -> CloudMetadata:
        return CloudMetadata.from_utils()


def track_carbon(
    fn: Callable = None,
    project_name: str = "codecarbon",
    measure_power_secs: int = 15,
    output_dir: str = ".",
    save_to_file: bool = True,
    offline: bool = False,
    country_iso_code: Optional[str] = None,
    country_name: Optional[str] = None,
    region: Optional[str] = None,
):
    """
    Decorator that supports both `CO2Tracker` and `OfflineCO2Tracker`
    :param fn: Function to be decorated
    :param project_name: Project name for current experiment run, default name as "codecarbon"
    :param measure_power_secs: Interval (in seconds) to measure hardware power usage, defaults to 15
    :param output_dir: Directory path to which the experiment details are logged
                       in a CSV file called `emissions.csv`, defaults to current directory
    :param save_to_file: Indicates if the emission artifacts should be logged to a file, defaults to True
    :param offline: Indicates if the tracker should be run in offline mode
    :param country_iso_code: 3 letter ISO Code of the country where the experiment is being run,
                             required if `offline=True`
    :param country_name: Name of the country where the experiment is being run,
                         required if `offline=True`
    :param region: The provincial region, for example, California in the US.
                   Currently, this only affects calculations for the United States
    :return: The decorated function
    """

    def _decorate(fn: Callable):
        @wraps(fn)
        def wrapped_fn(*args, **kwargs):
            if offline:
                if country_iso_code is None:
                    raise Exception("Needs ISO Code of the Country for Offline mode")
                tracker = OfflineCarbonTracker(
                    project_name=project_name,
                    measure_power_secs=measure_power_secs,
                    output_dir=output_dir,
                    save_to_file=save_to_file,
                    country_iso_code=country_iso_code,
                    country_name=country_name,
                    region=region,
                )
                tracker.start()
                fn(*args, **kwargs)
                tracker.stop()
            else:
                tracker = CarbonTracker(
                    project_name=project_name,
                    measure_power_secs=measure_power_secs,
                    output_dir=output_dir,
                    save_to_file=save_to_file,
                )
                tracker.start()
                fn(*args, **kwargs)
                tracker.stop()

        return wrapped_fn

    if fn:
        return _decorate(fn)
    return _decorate
