.. _parameters:

Input Parameters
================

A set of parameters are supported by API to help users provide additional details per project.

CO2Tracker
----------

The online mode object ``CO2Tracker`` takes following input parameters.

.. list-table:: Input Parameters to CO2Tracker
   :widths: 20 80
   :header-rows: 1

   * - Parameters
     - Description
   * - project_name
     - Name of the project, defaults to ``co2tracker``
   * - measure_power_secs
     - Interval (in seconds) to measure hardware power usage, defaults to ``15``
   * - output_dir
     - | Directory path to which the experiment details are logged
       | in a CSV file called ``emissions.csv``, defaults to current directory
   * - save_to_file
     - | Boolean variable indicating if the emission artifacts should be logged
       | to a CSV file at ``output_dir/emissions.csv``, defaults to ``True``


OfflineCO2Tracker
-----------------

The offline mode object ``OfflineCO2Tracker`` takes following input parameters.

.. list-table:: Input Parameters to OfflineCO2Tracker
   :widths: 20 80
   :header-rows: 1

   * - Parameters
     - Description
   * - country_iso_code
     - 3 letter ISO Code of the country where the experiment in being run
   * - country_name
     - Name of the country where the experiment in being run
   * - region
     - | Optional Name of the Province/State/City, where the infrastructure is hosted
       | Currently, supported only for US States
       | for example - California or New York
   * - project_name
     - Name of the project, defaults to ``co2tracker``
   * - measure_power_secs
     - Interval (in seconds) to measure hardware power usage, defaults to ``15``
   * - output_dir
     - | Directory path to which the experiment details are logged
       | in a CSV file called ``emissions.csv``, defaults to current directory
   * - save_to_file
     - | Boolean variable indicating if the emission artifacts should be logged
       | to a CSV file at ``output_dir/emissions.csv``, defaults to ``True``


@track_co2
----------

Decorator ``track_co2`` takes following input parameters.

.. list-table:: Input Parameters to @track_co2
   :widths: 20 80
   :header-rows: 1

   * - Parameters
     - Description
   * - project_name
     - Name of the project, defaults to ``co2tracker``
   * - measure_power_secs
     - Interval (in seconds) to measure hardware power usage, defaults to ``15``
   * - output_dir
     - | Directory path to which the experiment details are logged
       | in a CSV file called ``emissions.csv``, defaults to current directory
   * - save_to_file
     - | Boolean variable indicating if the emission artifacts should be logged
       | to a CSV file at ``output_dir/emissions.csv``, defaults to ``True``
   * - offline
     - Boolean variable indicating if the tracker should be run in offline mode, defaults to ``False``
   * - country_iso_code
     - 3 letter ISO Code of the country where the experiment in being run
   * - country_name
     - Name of the country where the experiment in being run
   * - region
     - | Optional Name of the Province/State/City, where the infrastructure is hosted
       | Currently, supported only for US States
       | for example - California or New York
