
RAPL Metrics
------------
RAPL (Running Average Power Limit) is a feature of modern processors that provides energy consumption measurements through hardware counters.

See https://blog.chih.me/read-cpu-power-with-RAPL.html for more information.

Despite the name "Intel RAPL", it supports AMD processors since Linux kernel 5.8.

Due to the `CVE-2020-8694 security issue <https://www.cve.org/CVERecord?id=CVE-2020-8694>`_ from 2020, all Linux distributions have changed right permission of the RAPL file, to reserve it to superuser.

There is a workaround, thanks to `prometheus/node_exporter#1892 <https://github.com/prometheus/node_exporter/issues/1892>`_:

.. code-block:: sh
    sudo apt install sysfsutils
    nano /etc/sysfs.conf
    # Add this line :
    mode class/powercap/intel-rapl:0/energy_uj = 0444
    reboot

Without rebooting you could do ``sudo chmod -R a+r /sys/class/powercap/*`` but it will be lost at next boot.

If you want more security you could create a specific group, add your user to this group and set group read permission only.

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

2. **psys can be unreliable**: While ``psys`` provides total platform power, it:

   - Can report higher values than expected (includes chipset, PCIe, etc.)
   - May not include all CPU components on older Intel systems : on some computers, ``psys`` is lower than ``package``.
   - So it is disabled by default, you can enable it with ``prefer_psys=True`` if desired

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
