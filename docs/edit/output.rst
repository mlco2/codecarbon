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
   * - experiment_id
     - A unique identifier using uuid library
   * - timestamp
     - Time of the experiment in ``%Y-%m-%dT%H:%M:%S`` format
   * - project_name
     - Name of the project, defaults to ``codecarbon``
   * - duration
     - Duration of the compute, in seconds
   * - emissions
     - Emissions as CO₂-equivalents [CO₂eq], in kg
   * - energy_consumed
     - Total Power consumed by the underlying infrastructure, in kWh
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

..  note::

    Developers can enhance the Output interface, based on requirements for example to log into a database, by implementing a custom Class
    that is a derived implementation of base class ``BaseOutput`` at ``codecarbon/output.py``
