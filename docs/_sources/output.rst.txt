.. _output:

Output
======

The package has an in-built logger that logs data into a CSV file named ``emissions.csv`` in the ``output_dir``, provided as an
input parameter [defaults to current directory], for each experiment tracked across projects.


.. list-table:: Data Fields Logged for each Experiment
   :widths: 20 80
   :align: center
   :header-rows: 1

   * - Fields
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
     - emissions divided per duration
   * - cpu_power
     - CPU power 
   * - gpu_power
     - GPU power 
   * - ram_power
     - RAM power 
   * - cpu_energy
     - Energy used per CPU
   * - gpu_energy
     - Energy used per GPU
   * - ram_energy
     - Energy used per RAM
   * - energy_consumed
     - sum of cpu_energy, gpu_energy and ram_energy
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
     - exemple ``Intel(R) Core(TM) i7-1065G7 CPU @ 1.30GHz``
   * - gpu_count
     - number of GPU
   * - gpu_model
     - model of gpu
   * - longitude
     - longitude
   * - latitude
     - latitude
   * - ram_total_size
     -  total RAM aviable
   * - Tracking_mode:
     - default to machin
   

..  note::

    Developers can enhance the Output interface, based on requirements for example to log into a database, by implementing a custom Class
    that is a derived implementation of base class ``BaseOutput`` at ``codecarbon/output.py``
