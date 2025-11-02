.. _parameters:

Parameters
================

A set of parameters are supported by API to help users provide additional details per project.

Input Parameters
-----------------

.. list-table:: Input Parameters
   :widths: 20 80
   :align: center
   :header-rows: 1

   * - Parameter
     - Description
   * - project_name
     - Name of the project, defaults to ``codecarbon``
   * - experiment_id
     - Id of the experiment
   * - measure_power_secs
     - Interval (in seconds) to measure hardware power usage, defaults to ``15``
   * - tracking_mode
     - | ``machine`` measure the power consumptions of the entire machine (default)
       | ``process`` try and isolate the tracked processes in isolation
   * - gpu_ids
     - | Comma-separated list of GPU ids to track, defaults to ``None``
       | These can either be integer indexes of GPUs on the system, or prefixes
       | to match against GPU identifiers as described `here <https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#cuda-environment-variables>`_
   * - log_level
     - | Global codecarbon log level (by order of verbosity): "debug", "info" (default),
       | "warning", "error", or "critical"
   * - co2_signal_api_token
     - | API token for co2signal.com (requires sign-up for free beta)
   * - pue
     - | PUE (Power Usage Effectiveness) of the data center
       | where the experiment is being run.
   * - wue
     - | WUE (Water Usage Effectiveness) of the data center
       | where the experiment is being run.
       | Units of *L/kWh* - how many litres of water are consumed per kilowatt-hour
       | of electricity consumed.
   * - force_cpu_power
     - | Force the CPU max power consumption in watts,
       | use this if you know the TDP of your machine.
       | *(POWER_CONSTANT x CONSUMPTION_PERCENTAGE)*
   * - force_ram_power
     - | Force the RAM power consumption in watts,
       | use this if you know the power consumption of your RAM.
       | Estimate it with ``sudo lshw -C memory -short | grep DIMM``
       | to get the number of RAM slots used, then do
       | *RAM power in W = Number of RAM Slots * 5 Watts*
   * - rapl_include_dram
     - | Boolean variable indicating if DRAM (memory) power should be included
       | in RAPL measurements on Linux systems, defaults to ``True``.
       | When ``True``, measures complete hardware power (CPU package + DRAM).
       | Set to ``False`` to measure only CPU package power.
       | Note: Only affects systems where RAPL exposes separate DRAM domains.
   * - rapl_prefer_psys
     - | Boolean variable indicating if psys (platform/system) RAPL domain should be
       | preferred over package domains on Linux systems, defaults to ``False``.
       | When ``True``, uses psys domain for total platform power (CPU + chipset + PCIe).
       | When ``False`` (default), uses package domains which are more reliable and
       | consistent with CPU TDP specifications.
       | Note: psys can report higher values than CPU TDP and may be unreliable on older systems.
   * - allow_multiple_runs
     - | Boolean variable indicating if multiple instance of CodeCarbon
       | on the same machine is allowed,
       | defaults to ``True`` since v3. Used to be ``False`` in v2.

PUE is a multiplication factor provided by the user, so it is up to the user to get it from their cloud provider.
Old data-centers have a PUE up to 2.2, where new greener ones could be as low as 1.1.

If you, or your provider, use ``CUDA_VISIBLE_DEVICES`` to set the GPUs you want to use, CodeCarbon will automaticly populate this value into ``gpu_ids``.
If you set ``gpu_ids`` manually, it will override the ``CUDA_VISIBLE_DEVICES`` for CodeCarbon measures.

Output parameters
-----------------

.. list-table:: Output Parameters
   :widths: 20 80
   :align: center
   :header-rows: 1

   * - Parameter
     - Description
   * - **save_to_file**
     - | Boolean variable indicating if the emission artifacts should be logged
       | to a CSV file, defaults to ``True``
   * - output_dir
     - | Directory path to which the experiment details are logged
       | defaults to current directory
   * - output_file
     - | Name of output CSV file
       | defaults to ``emissions.csv``
   * - on_csv_write
     - | When calling ``tracker.flush()`` manually choose if
       | - ``update`` the existing ``run_id`` row (erasing former data)
       | - ``append`` add a new row to CSV file (defaults)
   * - **save_to_api**
     - | Boolean variable indicating if emissions artifacts should be logged
       | to the CodeCarbon API, defaults to ``False``
   * - api_endpoint:
     - | Optional URL of CodeCarbon API endpoint for sending emissions data
       | defaults to "https://api.codecarbon.io"
   * - api_key
     - API key for the CodeCarbon API (mandatory to use this API!)
   * - api_call_interval
     - | Number of measurements between API calls (defaults to 8):
       | -1 : call API on flush() and at the end
       | 1 : at every measure
       | 2 : at every 2 measure, and so on
   * - **save_to_logger**
     - | Boolean variable indicating if the emission artifacts should be written
       | to a dedicated logger, defaults to ``False``
   * - logging_logger
     - LoggerOutput object encapsulating a logging.Logger or a Google Cloud logger
   * - logger_preamble
     - String to systematically include in the logger's messages (defaults to "")
   * - save_to_prometheus
     - | Boolean variable indicating if the emission artifacts should be written
       | to a Prometheus server, defaults to ``False``
   * - prometheus_url
     - | URL of the Prometheus server
   * - save_to_logfire
     - | Boolean variable indicating if the emission artifacts should be written
       | to a LogFire server, defaults to ``False``
   * - output_handlers
     - | List of output handlers to use for saving the emissions data
       | defaults to ``[]``

Specific parameters for offline mode
------------------------------------
.. list-table:: Input Parameters to OfflineEmissionsTracker
   :widths: 20 80
   :align: center
   :header-rows: 1

   * - Parameter
     - Description
   * - country_iso_code
     - | 3-letter ISO Code of the country
       | where the experiment is being run.
       | Available countries are listed in `global_energy_mix.json <https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/private_infra/global_energy_mix.json>`__
   * - region
     - | Optional name of the Province/State/City, where the infrastructure is hosted
       | Currently, supported only for US States and Canada
       | for example - California or New York, from the `list <https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/private_infra/2016/usa_emissions.json>`_
   * - cloud_provider
     - | The cloud provider specified for estimating emissions intensity,
       | defaults to ``None``. See `impact.csv <https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/cloud/impact.csv>`_ for a list of cloud providers
   * - cloud_region
     - | The region of the cloud data center, defaults to ``None``
       | See `impact.csv <https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/cloud/impact.csv>`_ for a list of cloud regions.
   * - country_2letter_iso_code
     - | For use with the Electricity Maps emissions API.
       | See `Electricity Maps zones <http://api.electricitymap.org/v3/zones>`_ for a list of codes and their locations.


@track_emissions
----------------

Decorator ``track_emissions`` in addition to standard arguments, requires the following parameters:

.. list-table:: Input Parameters to @track_emissions
   :widths: 20 80
   :align: center
   :header-rows: 1

   * - Parameter
     - Description
   * - fn
     - function to be decorated
   * - offline
     - | Boolean variable indicating if the tracker should be run in offline mode
       | defaults to ``False``
   * - country_iso_code
     - | 3 letter ISO Code of the country where the experiment is being run.
       | Available countries are listed in `global_energy_mix.json <https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/private_infra/2016/global_energy_mix.json>`__
   * - region
     - | Optional Name of the Province/State/City, where the infrastructure is hosted
       | Currently, supported only for US States
       | for example - California or New York, from the `list <https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/private_infra/2016/usa_emissions.json>`_
   * - cloud_provider
     - | The cloud provider specified for estimating emissions intensity,
       | defaults to ``None``. See `impact.csv <https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/cloud/impact.csv>`_ for a list of cloud providers
   * - cloud_region
     - | The region of the cloud data center, defaults to ``None``
       | See `impact.csv <https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/cloud/impact.csv>`_ for a list of cloud regions.
