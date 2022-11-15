.. _output:

Output
======

The package has an in-built logger that logs data into a CSV file named ``emissions.csv`` in the ``output_dir``, provided as an
input parameter (defaults to the current directory), for each experiment tracked across projects.


.. list-table:: Data Fields Logged for Each Experiment
   :widths: 20 80
   :align: center
   :header-rows: 1

   * - Field
     - Description
   * - timestamp
     - Time of the experiment in ``%Y-%m-%dT%H:%M:%S`` format
   * - project_name
     - Name of the project, defaults to ``codecarbon``
   * - run-id
     - id of the run
   * - duration
     - Duration of the compute, in seconds
   * - emissions
     - Emissions as CO₂-equivalents [CO₂eq], in kg
   * - emissions_rate
     - emissions divided per duration, in g/s
   * - cpu_power
     - CPU power (W)
   * - gpu_power
     - GPU power (W)
   * - ram_power
     - RAM power (W)
   * - cpu_energy
     - Energy used per CPU (kW)
   * - gpu_energy
     - Energy used per GPU (kW)
   * - ram_energy
     - Energy used per RAM (kW)
   * - energy_consumed
     - sum of cpu_energy, gpu_energy and ram_energy (kW)
   * - country_name
     - Name of the country where the infrastructure is hosted
   * - country_iso_code
     - 3-letter alphabet ISO Code of the respective country
   * - region
     - Province/State/City where the compute infrastructure is hosted
   * - on_cloud
     - ``Y`` if the infrastructure is on cloud, ``N`` in case of private infrastructure
   * - cloud_provider
     - One of the 3 major cloud providers, ``aws/azure/gcp``
   * - cloud_region
     - | Geographical Region for respective cloud provider,
       | examples ``us-east-2 for aws, brazilsouth for azure, asia-east1 for gcp``
   * - os
     - | os on the device
       | example ``Windows-10-10.0.19044-SP0``
   * - python_version
     - example ``3.8.10``
   * - cpu_count:
     - number of CPU
   * - cpu_model
     - example ``Intel(R) Core(TM) i7-1065G7 CPU @ 1.30GHz``
   * - gpu_count
     - number of GPU
   * - gpu_model
     - example ``1 x NVIDIA GeForce GTX 1080 Ti``
   * - longitude
     - | Longitude, with reduced precision to a range of 11.1 km / 123 km².
       | This is done for privacy protection.
   * - latitude
     - | Latitude, with reduced precision to a range of 11.1 km / 123 km².
       | This is done for privacy protection.
   * - ram_total_size
     -  total RAM aviable (Go)
   * - Tracking_mode:
     - ``machine`` or ``process``(default to ``machine``)

..  note::

    Developers can enhance the Output interface, based on requirements. For example, to log into a database, by implementing a custom Class
    that is a derived implementation of base class ``BaseOutput`` at ``codecarbon/output.py``
