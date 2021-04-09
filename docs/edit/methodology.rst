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
   * - Renewable (hydroelectricity, wind power, solar, etc.)
     - 0

In this analysis, we assigned low-carbon fuels (e.g., hydroelectricity, biomass) a Carbon Intensity of zero because the carbon footprint during electricity generation (for example, water flowing through a hydroelectric dam's turbine) approaches zero, but varies somewhat based on local variation in the type of low-carbon fuel used. There will be low, but distinct from one another, carbon dioxide emissions for biomass from wood combustion versus biomass from recycled landfill waste. Furthermore, these Carbon Intensities do not account for emissions from construction of electrical infrastructure and transport of fuels. If these factors were included, low-carbon fuels would have a nonzero Carbon Intensity—-but fossil fuel Carbon Intensities would be significantly higher than the values used here. We therefore consider low-carbon fuels' direct carbon emissions to be zero for the purposes of our project.


Localization
------------

The local energy mix is based on the specific location where code is run. In the included visualizations, global benchmarks can be seen. Once a location is determined, the amount of electricity from fossil fuel and renewable sources is used to define the local Energy Mix.

For example, in case the Energy Mix of the Grid Electricity is 25% Coal, 35% Petroleum, 26% Natural Gas and 14% Renewable:

.. code-block:: text

    Net Carbon Intensity = 0.25 * 996 + 0.35 * 817 + 0.26 * 744 + 0.14 * 0 = 728.39 kgCO₂/MWh

We derive the international energy mixes from the most recent year available in the United States' Energy Information Administration's Emissions & Generation Resource Integrated Database (eGRID; 2016). We approximate the energy mixes by examining the share of total primary energy produced and consumed for each country in the dataset and determining the proportion of energy derived from fossil fuel and low-carbon sources. However, because total primary energy includes sources other than electricity generation, this may marginally overstate carbon emissions by overemphasizing fossil fuels' contribution to the electrical grid in countries that use fossil fuels in other, non-energy sectors. Our estimate approximates values reported in other publications, however, because petroleum as a source of electrical generation will frequently have a higher Carbon Intensity than our average parameter (817 kgCO₂/MWh). Thus, the default CodeCarbon dataset produces global coverage of carbon emissions from electricity generation at the expense of some precision in the calculation.

We plan to refine and improve this approach in the future. First, we plan to update our default file to the most recent information available from eGRID (2017–2018) and will continue to refine this dataset as additional information is released. Second, we plan to add a more precise data layer that includes recent, specific information regarding countries' energy grid, including a verified source for that information. Combining these approaches will allow CodeCarbon to continue to provide global coverage while making more precise estimates of the carbon footprint of calculations made on the local electricity grid.

Potential collaborations on this aspect of CodeCarbon's methodology are welcome: if you would like to contribute data, techniques, or expertise, please contact us.


Power Usage
-----------
Power supply to the underlying hardware is tracked at frequent time intervals. This is a configurable parameter
``measure_power_secs``, with default value 15 seconds, that can be passed when instantiating the emissions tracker.

If none of the tracking tools are available on a computing resource, CodeCarbon will be switched to a fall back mode: It will first detect which CPU hardware is currently in use, and then map it to a data source listing 2000+ Intel and AMD CPUs and their corresponding thermal design powers (TDPs). If the CPU is not found in the data source, a global constant will be applied. CodeCarbon assumes that 50% of the TDP will be the average power consumption to make this approximation. We could not find any good resource showing statistical relationships between TDP and average power so we empirically tested that 50% is a decent approximation.

The net Power Used is the net power supply consumed during the compute time, measured as ``kWh``.


References
----------
`Energy Usage Reports: Environmental awareness as part of algorithmic accountability <https://arxiv.org/pdf/1911.08354.pdf>`_
