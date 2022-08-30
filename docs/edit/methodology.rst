.. _methodology:

Methodology
===========
Carbon dioxide (CO₂) emissions, expressed as kilograms of CO₂-equivalents [CO₂eq], are the products of two main factors :

.. code-block:: text

    C = Carbon Intensity of the electricity consumed for computation: quantified as kg of CO₂ emitted per kilowatt-hour of electricity.

    P = Power Consumed by the computational infrastructure: quantified as kilowatt-hours.

Carbon dioxide emissions (CO₂eq) can then be calculated as ``C * P``


Carbon Intensity
----------------
Carbon Intensity of the electricity consumed is calculated as a weighted average of the emissions from different
energy sources that are used to generate electricity, including fossil fuels and renewables. In this toolkit, the fossil fuels coal, petroleum, and natural gas are associated with specific carbon intensities: a known amount of carbon dioxide is emitted for each kilowatt-hour of electricity generated. Renewable or low-carbon fuels include solar power, hydroelectricity, biomass, geothermal, and more. The nearby energy grid contains a mixture of fossil fuels and low-carbon energy sources, called the Energy Mix. Based on the mix of energy sources in the local grid, this package calculates the Carbon Intensity of the electricity consumed.

.. image:: ./images/grid_energy_mix.png
            :align: center
            :alt: Grid Energy Mix
            :height: 300px
            :width: 350px

When aviable, CodeCarbon use global carbon intensity of electricity per cloud providers ( `here <https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/cloud/impact.csv>`_ ) or per countries ( `here <https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/private_infra/eu-carbon-intensity-electricity.csv>`_ ).

If we don't have the global carbon intensity or electricity of a country but we have it's electricity mix, we compute the carbon intensity of electricity using this table :

.. list-table:: Carbon Intensity Across Energy Sources
   :widths: 50 50
   :align: center
   :header-rows: 1

   * - Energy Source
     - Carbon Intensity (kg/MWh)
   * - Coal
     - 995
   * - Petroleum
     - 816
   * - Natural Gas
     - 743
   * - Geothermal
     - 38
   * - Hydroelectricity
     - 26
   * - Nuclear
     - 29
   * - Solar 
     - 48
   * - Wind
     - 26
   
sources: 
 -  `for fossil energies <https://github.com/responsibleproblemsolving/energy-usage#conversion-to-co2>`_ 
 - `for renewables energies <http://www.world-nuclear.org/uploadedFiles/org/WNA/Publications/Working_Group_Reports/comparison_of_lifecycle.pdf>`_  


Then if for example, in case the Energy Mix of the Grid Electricity is 25% Coal, 35% Petroleum, 26% Natural Gas and 14% Nuclear:

.. code-block:: text

    Net Carbon Intensity = 0.25 * 995 + 0.35 * 816 + 0.26 * 743 + 0.14 * 29 = 731.59 kgCO₂/kWh

If ever we have neither the global carbon intensity of a country nor it's electricity mix, we apply a world avarage of 475 gCO2.eq/KWh ( `source <https://www.iea.org/reports/global-energy-co2-status-report-2019/emissions>`_ )

As you can see, we try to be as accurate as possible estimating carbon intensity of electricity. Still there is room for improvement and all contribution are welcome.


Power Usage
-----------
Power supply to the underlying hardware is tracked at frequent time intervals. This is a configurable parameter
``measure_power_secs``, with default value 15 seconds, that can be passed when instantiating the emissions tracker.

If none of the tracking tools are available on a computing resource, CodeCarbon will be switched to a fall back mode: It will first detect which CPU hardware is currently in use, and then map it to a data source listing 2000+ Intel and AMD CPUs and their corresponding thermal design powers (TDPs). If the CPU is not found in the data source, a global constant will be applied. CodeCarbon assumes that 50% of the TDP will be the average power consumption to make this approximation. We could not find any good resource showing statistical relationships between TDP and average power so we empirically tested that 50% is a decent approximation.

The net Power Used is the net power supply consumed during the compute time, measured as ``kWh``.


References
----------
`Energy Usage Reports: Environmental awareness as part of algorithmic accountability <https://arxiv.org/pdf/1911.08354.pdf>`_
