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

Carbon Intensity of each individual fossil fuel source (e.g., coal, petroleum, natural gas) is based on measured carbon dioxide output and power generation in the United States. These values were applied worldwide: electricity from coal generation in Germany is assigned the same Carbon Intensity as electricity from coal generation in Japan. 


.. list-table:: Carbon Intensity Across Energy Sources
   :widths: 50 50
   :header-rows: 1

   * - Energy Source
     - Carbon Intensity (kg/MWh)
   * - Coal
     - 996
   * - Petroleum
     - 817
   * - Natural Gas
     - 744
   * - Renewable (hydroelectricity, wind power, solar, etc.)
     - 0

In this analysis, we assigned low-carbon fuels (e.g., hydroelectricity, biomass) a Carbon Intensity of zero because the carbon footprint during electricity generation (for example, water flowing through a hydroelectric dam's turbine) approaches zero, but varies somewhat based on local variation in the type of low-carbon fuel used. There will be low, but distinct from one another, carbon dioxide emissions for biomass from wood combustion versus biomass from recycled landfill waste. Furthermore, these Carbon Intensities do not account for emissions from construction of electrical infrastructure and transport of fuels. If these factors were included, low-carbon fuels would have a nonzero Carbon Intensity—-but fossil fuel Carbon Intensities would be significantly higher than the values used here. We therefore consider low-carbon fuels' direct carbon emissions to be zero for the purposes of our project.

Localization
------------

The local energy mix is based on the specific location where code is run. In the included visualizations, global benchmarks can be seen. Once a location is determined, the amount of electricity from fossil fuel and renewable sources is used to define the local Energy Mix.

For example, in case the Energy Mix of the Grid Electricity is 25% Coal, 35% Petroleum, 26% Natural Gas and 14% Renewable:

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
