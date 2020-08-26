.. _visualize:

Visualize
=========

The package also comes with a ``Dash App`` containing illustrations to understand the emissions logged from various experiments across projects.
The App currently consumes logged information from a CSV file, generated from an in-built logger in the package.

The App can be run by executing the below CLI command that needs following arguments:

- ``filepath`` - path to the CSV file containing logged information across experiments and projects
- ``port`` - an optional port number, in case default [8050] is used by an existing process

.. code-block:: bash

    co2board --filepath="examples/emissions.csv" --port=3333


Summary and Equivalents
-----------------------
Users can get an understanding into net power consumption and emissions generated across projects and can dive into a particular project.
The App also provides exemplary equivalents from daily life, for example:

- Weekly Share of an average American household
- Number of miles driven
- Time of 32-inch LCD TV watched

.. image:: ./images/summary.png
            :align: center
            :alt: Summary
            :height: 400px
            :width: 700px


Regional Comparisons
--------------------
The App also provides a comparative visual to benchmark emissions and energy mix of the electricity from the Grid across countries.

.. image:: ./images/global_equivalents.png
            :align: center
            :alt: Global Equivalents
            :height: 480px
            :width: 750px


Cloud Regions
-------------
The App also benchmarks equivalent emissions across different regions of the cloud provider being used and recommends the most eco-friendly
region to host infrastructure for the concerned cloud provider.

.. image:: ./images/cloud_emissions.png
            :align: center
            :alt: Cloud Emissions
            :height: 450px
            :width: 750px

