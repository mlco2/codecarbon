.. _methodology:

Methodology
===========
CO₂-equivalents [CO₂eq] is measured in kg of CO₂ emitted, which can be inferred from two main factors :

.. code-block:: text

    C = Carbon Intensity of the electricity consumed for compute, as kg of CO₂ emitted per kilowatt-hour.

    P = Power Consumed by the underlying infrastructure, as kilowatt-hour.

CO₂eq can then be calculated as ``C * P``


Carbon Intensity
----------------
Carbon Intensity of the electricity consumed is calculated as a weighted average of the emissions from different
energy sources, ``Coal, Petroleum, Natural Gas and Renewable`` that are used to generate electricity from the nearby grid.

.. image:: ./images/grid_energy_mix.png
            :align: center
            :alt: Grid Energy Mix
            :height: 300px
            :width: 350px


.. list-table:: Carbon Intensity Across Energy Sources
   :widths: 50 50
   :align: center
   :header-rows: 1

   * - Energy Source
     - Carbon Intensity (kg/MWh)
   * - Coal
     - 996
   * - Petroleum
     - 817
   * - Natural Gas
     - 744
   * - Low Carbon
     - 0

For example, in case the Energy Mix of the Grid Electricity is 25% Coal, 35% Petroleum, 26% Natural Gas and 14% Renewable.

.. code-block:: text

    Net Carbon Intensity = 0.25 * 996 + 0.35 * 817 + 0.26 * 744 + 0.14 * 0 = 728.39 kgCO₂/MWh


Power Usage
-----------
Power supply to the underlying hardware is tracked at frequent time intervals. This is a configurable parameter
``measure_power_secs``, with default value 15 seconds, that can be passed when instantiating the emissions tracker.

The net Power Used is the net power supply consumed during the compute time, measured as ``kWh``.


References
----------
`Energy Usage Reports: Environmental awareness as part of algorithmic accountability <https://arxiv.org/pdf/1911.08354.pdf>`_
