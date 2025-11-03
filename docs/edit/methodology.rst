.. _methodology:

Methodology
===========
Carbon dioxide (CO₂) emissions, expressed as kilograms of CO₂-equivalents [CO₂eq], are the product of two main factors :

.. code-block:: text

    C = Carbon Intensity of the electricity consumed for computation: quantified as g of CO₂ emitted per kilowatt-hour of electricity.

    E = Energy Consumed by the computational infrastructure: quantified as kilowatt-hours.

Carbon dioxide emissions (CO₂eq) can then be calculated as ``C * E``


Carbon Intensity
----------------
Carbon Intensity of the consumed electricity is calculated as a weighted average of the emissions from the different
energy sources that are used to generate electricity, including fossil fuels and renewables. In this toolkit, the fossil fuels coal, petroleum, and natural gas are associated with specific carbon intensities: a known amount of carbon dioxide is emitted for each kilowatt-hour of electricity generated. Renewable or low-carbon fuels include solar power, hydroelectricity, biomass, geothermal, and more. The nearby energy grid contains a mixture of fossil fuels and low-carbon energy sources, called the Energy Mix. Based on the mix of energy sources in the local grid, the Carbon Intensity of the electricity consumed can be computed.

.. image:: ./images/grid_energy_mix.png
            :align: center
            :alt: Grid Energy Mix
            :height: 300px
            :width: 350px

When available, CodeCarbon uses global carbon intensity of electricity per cloud provider ( `here <https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/cloud/impact.csv>`__) or per country ( `here <https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/private_infra/global_energy_mix.json>`__ ).

If we don't have the global carbon intensity or electricity of a country, but we have its electricity mix, we used to compute the carbon intensity of electricity using this table:

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

Sources:
 - `for fossil energies <https://github.com/responsibleproblemsolving/energy-usage#conversion-to-co2>`_
 - `for renewables energies <http://www.world-nuclear.org/uploadedFiles/org/WNA/Publications/Working_Group_Reports/comparison_of_lifecycle.pdf>`_


Then, for example, if the Energy Mix of the Grid Electricity is 25% Coal, 35% Petroleum, 26% Natural Gas and 14% Nuclear:

.. code-block:: text

    Net Carbon Intensity = 0.25 * 995 + 0.35 * 816 + 0.26 * 743 + 0.14 * 29 = 731.59 kgCO₂/kWh

But it doesn't happen anymore because Our World in Data now provides the global carbon intensity of electricity per country ( `source <https://ourworldindata.org/grapher/carbon-intensity-electricity#explore-the-data>`__ ). Some countries are missing data for last year, so we use the previous year data available.

If ever we have neither the global carbon intensity of a country nor it's electricity mix, we apply a world average of 475 gCO2.eq/KWh ( `source <https://www.iea.org/reports/global-energy-co2-status-report-2019/emissions>`__ ).

As you can see, we try to be as accurate as possible in estimating carbon intensity of electricity. Still there is room for improvement and all contributions are welcome.


Power Usage
-----------

Power supply to the underlying hardware is tracked at frequent time intervals. This is a configurable parameter
``measure_power_secs``, with default value 15 seconds, that can be passed when instantiating the emissions' tracker.

Currently, the package supports the following hardware infrastructure.

GPU
~~~~

Tracks Nvidia GPUs energy consumption using ``nvidia-ml-py`` library (installed with the package).

RAM
~~~~

CodeCarbon v2 uses a 3 Watts for 8 GB ratio `source <https://www.crucial.com/support/articles-faq-memory/how-much-power-does-memory-use>`__ .

But this is not a good measure because it doesn't take into account the number of RAM slots used in the machine, that really drive the power consumption, not the amount of RAM.
For example, in servers you could have thousands of GB of RAM but the power consumption would not be proportional to the amount of memory used, but to the number of memory modules used.

Old machine could use 2 Mb memory stick, where modern servers will use 128 Mb memory stick.

So, in CodeCarbon v3 we switch to using 5 Watts for each RAM slot. The energy consumption is calculated as follows:

.. code-block:: text

    RAM Power Consumption = 5 Watts * Number of RAM slots used

But getting the number of RAM slots used is not possible as you need root access to get the number of RAM slots used. So we use an heuristic based on the RAM size.

For example keep a minimum of 2 modules. Except for ARM CPU like rapsberry pi where we will consider a 3W constant. Then consider the max RAM per module is 128GB and that RAM module only exist in power of 2 (2, 4, 8, 16, 32, 64, 128). So we can estimate the power consumption of the RAM by the number of modules used.

- For ARM CPUs (like Raspberry Pi), a constant 3W will be used as the minimum power
- Base power per DIMM is 5W for x86 systems and 1.5W for ARM systems
- For standard systems (up to 4 DIMMs): linear scaling at full power per DIMM
- For medium systems (5-8 DIMMs): decreasing efficiency (90% power per additional DIMM)
- For large systems (9-16 DIMMs): further reduced efficiency (80% power per additional DIMM)
- For very large systems (17+ DIMMs): highest efficiency (70% power per additional DIMM)
- Ensures at least 10W for x86 systems (assuming 2 DIMMs at minimum)
- Ensures at least 3W for ARM systems

Example Power Estimates:

- **Small laptop (8GB RAM)**: ~10W (2 DIMMs at 5W each)
- **Desktop (32GB RAM)**: ~20W (4 DIMMs at 5W each)
- **Desktop (64GB RAM)**: ~20W (4 DIMMs at 5W each), the same as 32GB
- **Small server (128GB RAM)**: ~40W (8 DIMMs with efficiency scaling)
- **Large server (1TB RAM)**: ~40W (using 8x128GB DIMMs with high efficiency scaling)

This approach significantly improves the accuracy for large servers by recognizing that RAM power consumption doesn't scale linearly with capacity, but rather with the number of physical modules. Since we don't have direct access to the actual DIMM configuration, this heuristic provides a more reasonable estimate than the previous linear model.

If you know the exact RAM power consumption of your system, then provide it using the `force_ram_power` parameter, which will override the automatic estimation.

For example, in a Ubuntu machine, you can get the number of RAM slots used with the following command:

.. code-block:: bash

    sudo lshw -C memory -short | grep DIMM

    /0/37/0                                    memory         4GiB DIMM DDR4 Synchrone Unbuffered (Unregistered) 2400 MHz (0,4 ns)
    /0/37/1                                    memory         4GiB DIMM DDR4 Synchrone Unbuffered (Unregistered) 2400 MHz (0,4 ns)
    /0/37/2                                    memory         4GiB DIMM DDR4 Synchrone Unbuffered (Unregistered) 2400 MHz (0,4 ns)
    /0/37/3                                    memory         4GiB DIMM DDR4 Synchrone Unbuffered (Unregistered) 2400 MHz (0,4 ns)

Here we count 4 RAM slots used, so the power consumption will be 4 x 5 = 20 Watts, just add `force_ram_power=20` to the init of CodeCarbon.


CPU
~~~~

- **On Windows or Mac (Intel)**

Tracks Intel processors energy consumption using the ``Intel Power Gadget``. You need to install it yourself from this `source <https://www.intel.com/content/www/us/en/developer/articles/tool/power-gadget.html>`__ . But has been discontinued. There is a discussion about it on `github issues #457 <https://github.com/mlco2/codecarbon/issues/457>`_.

- **Apple Silicon Chips (M1, M2)**

Apple Silicon Chips contain both the CPU and the GPU.

Codecarbon tracks Apple Silicon Chip energy consumption using ``powermetrics``. It should be available natively on any mac.
However, this tool is only usable with ``sudo`` rights and to our current knowledge, there are no other options to track the energy consumption of the Apple Silicon Chip without administrative rights
(if you know of any solution for this do not hesitate and `open an issue with your proposed solution <https://github.com/mlco2/codecarbon/issues/>`_).

To give sudo rights without having to enter a password each time, you can modify the sudoers file with the following command:

.. code-block:: bash

    sudo visudo


Then add the following line at the end of the file:

.. code-block:: bash

    username ALL = (root) NOPASSWD: /usr/bin/powermetrics

If you do not want to give sudo rights to your user, then CodeCarbon will fall back to constant mode to measure CPU energy consumption.

- **On Linux**

Tracks Intel and AMD processor energy consumption from Intel RAPL files at ``/sys/class/powercap/intel-rapl/subsystem`` ( `reference <https://web.eece.maine.edu/~vweaver/projects/rapl/>`_ ).
All CPUs listed in this directory will be tracked.

*Note*: The Power Consumption will be tracked only if the RAPL files exist at the above-mentioned path and if the user has the necessary permissions to read them.


CPU hardware
------------

The CPU die is the processing unit itself. It's a piece of semiconductor that has been sculpted/etched/deposited by various manufacturing processes into a net of logic blocks that do stuff that makes computing possible. The processor package is what you get when you buy a single processor. It contains one or more dies, plastic/ceramic housing for dies and gold-plated contacts that match those on your motherboard.

In Linux kernel, energy_uj is a current energy counter in micro joules. It is used to measure CPU core's energy consumption.

Micro joules is then converted in kWh, with formulas kWh=energy * 10 ** (-6) * 2.77778e-7

For example, on a laptop with Intel(R) Core(TM) i7-7600U, Code Carbon will read two files :
/sys/class/powercap/intel-rapl/intel-rapl:1/energy_uj and /sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj


RAPL Metrics
------------
RAPL (Running Average Power Limit) is a feature of modern processors that provides energy consumption measurements through hardware counters.

See https://blog.chih.me/read-cpu-power-with-RAPL.html for more information.

Despite the name "Intel RAPL", it supports AMD processors since Linux kernel 5.8.

RAPL Domain Architecture
~~~~~~~~~~~~~~~~~~~~~~~~

RAPL exposes energy consumption data through files in ``/sys/class/powercap/`` with two interfaces:

- **intel-rapl** (MSR-based): Traditional Model-Specific Register interface, accessed via CPU instructions
- **intel-rapl-mmio** (Memory-Mapped I/O): Newer interface introduced for modern Intel processors (10th gen+)

Each domain is represented by a directory containing:

- ``name``: Domain identifier (e.g., "package-0", "core", "uncore", "psys")
- ``energy_uj``: Current energy counter in microjoules
- ``max_energy_range_uj``: Maximum value before counter wraps

Available RAPL Domains
~~~~~~~~~~~~~~~~~~~~~~

Different CPUs expose different domains. Common domains include:

- **psys** (Platform/System): Total platform power including CPU package, integrated GPU, memory controller, and some chipset components. **Most comprehensive measurement** on modern Intel systems (Skylake and newer).

- **package-0/package-N**: Entire CPU socket including:

  - All CPU cores
  - Integrated GPU (if present)
  - Last-level cache (LLC)
  - Memory controller
  - System agent/uncore

- **core**: Only the CPU compute cores (subset of package)

- **uncore**: Everything in the package except cores:

  - Memory controller (DDR interface on CPU)
  - Last-level cache
  - Ring interconnect between cores
  - Integrated GPU (if present)

- **dram**: Memory controller power (rare on consumer hardware, more common on servers)

- **gpu**: Discrete or integrated GPU (when available)

RAPL Domain Hierarchy and Double-Counting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Critical**: RAPL domains are hierarchical and overlapping. Summing them causes severe over-counting!

Example hierarchy on Intel Core Ultra 7 265H:

.. code-block:: text

    psys (9.6W) ← Most comprehensive, includes everything below
    ├── package-0 (3.8W) ← Subset of psys
    │   ├── core (0.8W) ← Subset of package
    │   └── uncore (0.2W) ← Subset of package
    └── Other platform components (~5W)
        └── Chipset, PCIe, etc.

**Wrong approach**: 9.6W + 3.8W + 0.8W + 0.2W = 14.4W ❌ (Triple counting!)

**Correct approach**: Use only psys (9.6W) ✅

CodeCarbon's RAPL Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~

CodeCarbon implements intelligent domain selection to provide reliable and consistent measurements:

1. **Prefer package domains (default)**: CodeCarbon prioritizes ``package`` domains because they:

   - Update reliably under CPU load
   - Match CPU TDP specifications
   - Provide consistent measurements across different Intel generations
   - Can be supplemented with ``dram`` domains for complete hardware measurement (package + DRAM)

2. **Optional psys mode**: Set ``prefer_psys=True`` to use ``psys`` (platform/system) domain instead:

   - Provides total platform power (CPU + chipset + PCIe + some other components)
   - More comprehensive but can report higher values than CPU TDP
   - May include non-CPU components affected by the computation
   - **Note**: On some older Intel systems (e.g., Kaby Lake), psys can report unexpectedly high values

3. **Interface deduplication**: When the same domain appears in both ``intel-rapl`` and ``intel-rapl-mmio``:

   - Detects duplicate domains by name
   - Prefers MMIO over MSR (newer, recommended interface)
   - Falls back to MSR if MMIO is unreadable

4. **Subdomain filtering**: Excludes ``core`` and ``uncore`` subdomains when ``package`` is available to avoid double-counting

5. **DRAM inclusion**: By default (``include_dram=True``), adds DRAM domain to package for complete hardware power measurement

Platform-Specific Behavior
~~~~~~~~~~~~~~~~~~~~~~~~~

**Intel processors**:

- Modern CPUs (Skylake+): Provide ``psys`` for comprehensive platform measurement
- ``core`` is included in ``package``
- ``package`` may include or exclude integrated GPU depending on model

**AMD processors**:

- ``core`` reports very low energy values
- Unclear if ``core`` is included in ``package`` (vendor documentation is sparse)
- Multiple dies may report as separate packages (e.g., Threadripper)

**What RAPL Does NOT Measure**:

- ❌ DRAM chips themselves (only memory controller)
- ❌ SSDs/NVMe drives
- ❌ Discrete GPUs (use nvidia-smi, rocm-smi separately)
- ❌ Motherboard chipset (unless included in psys)
- ❌ Fans, USB devices, peripherals
- ❌ Power supply inefficiency
- ❌ Discrete NPUs

For more details, see the excellent documentation from Scaphandre: https://hubblo-org.github.io/scaphandre-documentation/explanations/rapl-domains.html and discussion with references: https://github.com/hubblo-org/scaphandre/issues/116#issuecomment-854453231



.. image:: https://hubblo-org.github.io/scaphandre-documentation/explanations/rapl.png
    :align: center
    :alt: RAPL Example
    :width: 600px

Source :“RAPL in Action: Experiences in Using RAPL for Power Measurements,” (K. N. Khan, M. Hirki, T. Niemi, J. K. Nurminen, and Z. Ou, ACM Trans. Model. Perform. Eval. Comput. Syst., vol. 3, no. 2, pp. 1–26, Apr. 2018, doi: 10.1145/3177754.)

RAPL Measurements: Real-World Examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choosing the right metric to track CPU power consumption depends on CPU hardware and available domains. Below are measurements from different systems showing the importance of avoiding double-counting.

We investigate RAPL on various architectures :

- 2017 Gaming computer with AMD Ryzen Threadripper 1950X
- 2017 Laptop with Intel(R) Core(TM) i7-7600U (TDP 15W)
- 2025 Laptop with Intel(R) Core(TM) Ultra 7 265H (TDP 28W)


Desktop computer with AMD Ryzen Threadripper 1950X 16-Core (32 threads) Processor.
Power plug measure when idle (10% CPU): 125 W
package-0-die-0 : 68 W
package-0-die-1 : 68 W
CodeCarbon : 137 W

Laptop: Intel(R) Core(TM) Ultra 7 265H (TDP 28W)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Idle Measurements**:

.. code-block:: text

    Powertop battery discharge rate: 6W

    RAPL domains (individual readings):
    - psys (platform):    6.66W  ← Total platform power (BEST)
    - package-0:          3.85W  ← CPU package (subset of psys)
    - core:               0.35W  ← CPU cores only (subset of package)
    - uncore:             0.02W  ← Memory controller, cache (subset of package)

    ⚠️  WRONG: Summing all domains = 10.88W (over-counting!)
    ✅  CORRECT: Use psys only = 6.66W (matches battery discharge)

**CodeCarbon behavior**: Uses **psys only** (6.66W) to avoid double-counting.

**Under Load (stress-ng)**:

.. code-block:: text

    Powertop battery discharge rate: 27W

    RAPL domains:
    - psys:               24.69W  ← Total platform power (BEST)
    - package-0:          21.35W  ← CPU package (subset of psys)
    - core:               15.37W  ← CPU cores (subset of package)
    - uncore:              0.07W  ← Uncore (subset of package)

    ✅  CORRECT: Use psys only = 24.69W (close to battery discharge)

**CodeCarbon measurement**: 22W using psys (accurate, within expected range)

**Note**: The package-0 measurement (21.35W) excludes some platform components like chipset and PCIe that are included in psys (24.69W).

Laptop: Intel(R) Core(TM) i7-7600U (TDP 15W, 7th Gen Kaby Lake)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Idle Measurements**:

.. code-block:: text

    Powertop battery discharge rate: 9.31W

    RAPL domains:
    - psys:              12.21W  ← Total platform power (includes everything)
    - package-0:          1.44W  ← CPU package only
    - core:               0.46W  ← CPU cores (subset of package)
    - uncore:             0.04W  ← Uncore (subset of package)
    - dram:               0.54W  ← Memory controller (may overlap with uncore)

    ⚠️  WRONG: Summing all = 14.69W (triple counting!)
    ✅  CORRECT: Use psys = 12.21W

**Under Load (stress-ng)**:

.. code-block:: text

    Powertop battery discharge rate: 8.40W (unreliable during stress test)

    RAPL domains:
    - psys:              29.97W  ← Total platform power (BEST)
    - package-0:         15.73W  ← CPU package (matches TDP, subset of psys)
    - core:              14.00W  ← CPU cores (subset of package)
    - uncore:             0.54W  ← Uncore (subset of package)
    - dram:               1.23W  ← Memory controller power

    ⚠️  WRONG: Summing all = 61.47W (massive over-counting!)
    ✅  CORRECT: Use psys = 29.97W

    Analysis:
    - psys (29.97W) includes package (15.73W) + platform components (~14W)
    - package (15.73W) includes core (14.00W) + uncore (0.54W) + other
    - Core power (14.00W) matches the CPU TDP spec (15W)

**CodeCarbon behavior**: Uses **psys only** (29.97W) for accurate total platform measurement.

**Legacy behavior (before v2.x)**: Would have measured only package-0 (15.73W), missing ~14W of platform power!


Desktop: AMD Ryzen Threadripper 1950X (16-Core, 32 threads, Multi-die)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Idle Measurements (10% CPU load)**:

.. code-block:: text

    Wall power meter: 100W (whole system)


    RAPL domains:
        Monitoring domains:
        - core (intel-rapl:0:0) via MSR
        - package-0 (intel-rapl:0) via MSR

        Domain 'core' (MSR): 0.61 Watts
        Domain 'package-0' (MSR): 29.76 Watts
        Total Power Consumption: 30.37 Watts

        Domain 'core' (MSR): 0.20 Watts
        Domain 'package-0' (MSR): 38.62 Watts
        Total Power Consumption: 38.82 Watts

    [codecarbon INFO @ 22:24:44] 	RAPL - Monitoring domain 'package-0' (displayed as 'Processor Energy Delta_0(kWh)') via MSR at /sys/class/powercap/intel-rapl/subsystem/intel-rapl/intel-rapl:0/energy_uj

    ✅  CodeCarbon total: ~ 40 W

    Note: RAPL on this system measures only the CPU dies, not platform.
    Wall power includes motherboard, RAM, fans, PSU losses.

**Under Full Load (100% CPU, stress test)**:

.. code-block:: text

    Wall power meter: ~ 280 W total (131W above idle baseline)

    Monitoring domains:
    - core (intel-rapl:0:0) via MSR
    - package-0 (intel-rapl:0) via MSR

    Domain 'core' (MSR): 8.86 Watts
    Domain 'package-0' (MSR): 172.50 Watts
    Total Power Consumption: 181.36 Watts

    Domain 'core' (MSR): 8.88 Watts
    Domain 'package-0' (MSR): 172.16 Watts
    Total Power Consumption: 181.05 Watts

    ✅  CodeCarbon total: 171 W, in line with the TDP of 180 W
    280 - 100 (idle) = 180 W

    Analysis:
    - Each die independently measured via RAPL
    - No psys domain available on this AMD system
    - RAPL counter range: 234 sec at 280W (potential wraparound consideration)

**AMD RAPL Characteristics**:

- Multi-die CPUs report separate packages (package-0-die-0, package-0-die-1)
- No psys domain available on older AMD processors
- ``core`` domain reports very low values (unclear if included in package)
- Package measurements are generally reliable for total CPU power

Key Takeaways for RAPL Measurements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **CodeCarbon defaults to package domains**: This provides the most reliable and consistent measurements that match CPU TDP specifications. Package domains update correctly under load across all Intel generations.

2. **psys is optional but can be unreliable**: While ``psys`` provides total platform power, it:

   - Can report higher values than expected (includes chipset, PCIe, etc.)
   - May not update correctly on some systems (known firmware/kernel issues)
   - Is less consistent across different Intel generations
   - Can be enabled with ``prefer_psys=True`` if desired

3. **Avoid summing overlapping domains**: Never sum psys + package + core + uncore. They are hierarchical and overlapping. This causes 2-3x over-counting!

4. **Domain hierarchy**:

   - psys ⊃ package ⊃ {core, uncore}
   - Correct: Use package alone (CodeCarbon default) OR psys alone (with prefer_psys=True)
   - Wrong: Sum multiple levels

5. **Interface deduplication**: The same domain may appear in both ``intel-rapl`` (MSR) and ``intel-rapl-mmio`` interfaces. CodeCarbon automatically deduplicates, preferring MMIO.

6. **DRAM measurement**: CodeCarbon includes DRAM domains by default (``include_dram=True``) for complete hardware measurement (CPU package + memory). Set ``include_dram=False`` to measure only CPU package.

7. **Platform-specific behavior**:

   - Intel modern: package + dram (default) or psys (with prefer_psys=True)
   - Intel older: package-0 for CPU only
   - AMD: Sum all package-X-die-Y for multi-die CPUs

8. **Limitations**: RAPL does NOT measure:

   - Discrete GPUs (use nvidia-smi/rocm-smi)
   - SSDs, peripherals, fans
   - Actual DRAM chips (only memory controller on CPU)
   - Complete system power (use wall meter for accuracy)

CPU metrics priority
--------------------

CodeCarbon will first try to read the energy consumption of the CPU from low level interface like RAPL or ``powermetrics``.
If none of the tracking tools are available, CodeCarbon will be switched to a fallback mode:

- It will first detect which CPU hardware is currently in use, and then map it to a data source listing 2000+ Intel and AMD CPUs and their corresponding thermal design powers (TDPs).
- If the CPU is not found in the data source, a global constant will be applied.
- If ``psutil`` is available, CodeCarbon will try to estimate the energy consumption from the TDP and the CPU load.
- CodeCarbon assumes that 50% of the TDP will be the average power consumption to make this approximation.

Here is a drawing of the fallback mode:

.. image:: ./images/cpu_fallback.png
            :align: center
            :alt: CPU Fallback

The code doing this is available in `codecarbon/core/resource_tracker.py <https://github.com/mlco2/codecarbon/blob/master/codecarbon/core/resource_tracker.py#L24>`_.

The net Energy Used is the net power supply consumed during the compute time, measured as ``kWh``.

We compute energy consumption as the product of the power consumed and the time the power was consumed for. The formula is:
``Energy = Power * Time``

References
----------
`Energy Usage Reports: Environmental awareness as part of algorithmic accountability <https://arxiv.org/pdf/1911.08354.pdf>`_


How CodeCarbon Works
~~~~~~~~~~~~~~~~~~~~

CodeCarbon uses a scheduler that, by default, calls for a measure every 15 seconds, so it has no significant overhead.

The measure itself is fast and CodeCarbon is designed to be as light as possible with a small memory footprint.

The scheduler is started when the first ``start`` method is called and stopped when ``stop`` method is called.


Estimation of Equivalent Usage Emissions
----------------------------------------

The CodeCarbon dashboard provides equivalent emissions and energy usage comparisons to help users better understand the carbon impact of their activities. These comparisons are based on the following assumptions:

Car Usage
~~~~~~~~~

- **Emission factor**: *0.12 kgCO₂ per kilometer driven*.
- This value is derived from the average emissions of a European passenger car under normal driving conditions.

Source : `European Environment Agency <https://co2cars.apps.eea.europa.eu/?source=%7B%22track_total_hits%22%3Atrue%2C%22query%22%3A%7B%22bool%22%3A%7B%22must%22%3A%5B%7B%22constant_score%22%3A%7B%22filter%22%3A%7B%22bool%22%3A%7B%22must%22%3A%5B%7B%22bool%22%3A%7B%22should%22%3A%5B%7B%22term%22%3A%7B%22year%22%3A2023%7D%7D%5D%7D%7D%2C%7B%22bool%22%3A%7B%22should%22%3A%5B%7B%22term%22%3A%7B%22scStatus%22%3A%22Provisional%22%7D%7D%5D%7D%7D%5D%7D%7D%7D%7D%5D%7D%7D%2C%22display_type%22%3A%22tabular%22%7D>`_


TV Usage
~~~~~~~~

- **Energy consumption**: *138 Wh per day based on average use*.
- This assumes:
  - An average daily usage of 6.5 hours.
  - A modern television with a power consumption of approximately *21.2 W per hour*.

Source : `The French Agency for Ecological Transition <https://agirpourlatransition.ademe.fr/particuliers/maison/economies-denergie-deau/electricite-combien-consomment-appareils-maison>`_

US Citizen Weekly Emissions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Annual emissions**: *13.3 tons of CO₂ equivalent per year* for an average US citizen.
- **Weekly emissions**: This value is divided by the 52 weeks in a year to estimate weekly emissions:

.. math::
   \text{Weekly Emissions} = \frac{\text{Annual Emissions (tons)}}{52}

.. math::
   \text{Weekly Emissions} = \frac{13.3}{52} \approx 0.256 \, \text{tons of CO₂ equivalent per week.}

Source : `IEA CO2 total emissions per capita by region, 2000-2023 <https://www.iea.org/data-and-statistics/charts/co2-total-emissions-per-capita-by-region-2000-2023>`_

Calculation Formula
~~~~~~~~~~~~~~~~~~~

The equivalent emissions are calculated using this formula:

.. math::
   \text{Equivalent Emissions} = \frac{\text{Total Emissions (kgCO₂)}}{\text{Emission Factor (kgCO₂/unit)}}

For example:

- **Car Usage**: *1 kWh* of energy consumption is approximately equivalent to:

  - *8.33 kilometers driven by a car* (*1 ÷ 0.12*).
  - *11.9 hours of TV usage* (*1 ÷ 0.084*), if emissions are considered.

- **US Citizen Emissions**:

  - *1 kWh* of energy consumption can be compared to a fraction of the average weekly emissions of a US citizen:

.. math::
   \text{US Citizen Equivalent} = \frac{\text{Total Emissions (tons)}}{0.256}

These estimates are approximate and subject to regional variations in:
- Grid emissions intensity.
- Vehicle efficiencies.

Source Code
~~~~~~~~~~~

The emission factors used are defined in the `CodeCarbon source code <https://github.com/mlco2/codecarbon/blob/master/webapp/src/helpers/constants.ts>`_. They are based on publicly available data and general assumptions.
