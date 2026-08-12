# Accuracy and validation

This page describes what CodeCarbon measures, how close those measurements are
to a hardware reference, where the remaining error comes from, and what you can
do to reduce it.

## What is inside the measurement boundary

CodeCarbon reports the **direct electricity consumption of the compute
components it can read or estimate**: CPU, GPU and RAM. It then multiplies the
resulting energy by the carbon intensity of the local electricity grid.

Outside the boundary:

- disk I/O, network transfers, displays, cooling and other peripherals;
- power supply and datacenter overhead, unless you set a
  [PUE](../how-to/configuration.md) value yourself;
- life-cycle (embodied) emissions of the hardware.

Every accuracy statement below is scoped to that boundary. A CodeCarbon figure
is not a whole-facility footprint, and it is not meant to be one.

## How accurate each measurement backend is

CodeCarbon prefers hardware energy counters and falls back to estimation when no
counter is readable. The fallback order is documented in
[Methodology → CPU metrics priority](methodology.md#which-backend-gets-chosen).

| Backend | How it works | Agreement with a reference | When it is used |
|---|---|---|---|
| Intel RAPL | Reads hardware energy counters under `/sys/class/powercap/` | On the four CPUs profiled in this repository, CodeCarbon's RAPL readings matched `stress-ng --rapl` on the same machine. RAPL is itself an on-die estimate and its own absolute error is not characterised here. | Linux, Intel and AMD (kernel ≥ 5.8), when the counters are readable |
| NVML (NVIDIA) | Reads accumulated board energy from the driver (`nvmlDeviceGetTotalEnergyConsumption`) | Not yet measured against an external reference | Any NVIDIA GPU with a working driver |
| amdsmi (AMD) | Reads the driver energy counter (`amdsmi_get_energy_count`) | Not yet measured against an external reference | AMD GPUs |
| macOS `powermetrics` | System power reporting | Not yet measured against an external reference | macOS, Intel and Apple Silicon |
| Windows EMI | Energy Meter Interface | Not yet measured against an external reference | Windows 11, where the platform exposes it |
| Intel Power Gadget | Vendor tool, deprecated upstream | Not yet measured | Legacy path |
| CPU load × TDP | Estimates power from CPU utilisation against the TDP listed in `cpu_power.csv`. Two different curves, [selected by `tracking_mode`](methodology.md#the-two-cpu_load-models) | See the profiling results below: in **machine mode**, on the machines profiled, the estimate deviated from RAPL by roughly −60% to +90% depending on CPU and load point. Process mode is uncharacterised | Fallback when no CPU counter is available |
| Default watts per thread | Estimates from thread count alone | Not characterised; this is the least accurate path | Last resort, when the CPU model is absent from `cpu_power.csv` |

### The CPU load × TDP fallback, measured

`examples/compare_cpu_load_and_RAPL.py` sweeps CPU load with `stress-ng` and
records, at each load point, both the RAPL reading and the TDP-based estimate
CodeCarbon would have produced. The raw sweeps live in
`codecarbon/data/hardware/cpu_load_profiling/` and are plotted in
`examples/compare_cpu_load_and_RAPL.ipynb`. Runs are dated January 2025.

!!! warning "These figures are machine mode only"

    The profiling script constructs its tracker with `force_mode_cpu_load=True`
    and no `tracking_mode` argument (`compare_cpu_load_and_RAPL.py:289-292`), so
    every number below was gathered under the default
    `tracking_mode="machine"`.

    That matters because `cpu_load` mode uses a **different power model** in
    process mode — linear with no idle floor, rather than cubic with a 10%-of-TDP
    floor. See
    [Methodology → The two cpu_load models](methodology.md#the-two-cpu_load-models).
    **The deviations below do not transfer to `tracking_mode="process"`.** No
    equivalent profiling has been done for process mode.

Deviation of the estimate from the RAPL reading, over load points above 5%
(negative means the estimate is lower than RAPL):

| CPU | At full load | Range across load points |
|---|---|---|
| Dual Intel Xeon E5-2620 v3 (24 threads) | +40% | +2% to +59% |
| Intel Xeon E3-1240 v2 (8 threads) | +37% | +20% to +187% |
| AMD Ryzen Threadripper 1950X (32 threads) | +3% | −57% to +18% |
| AMD EPYC 8024P (16 threads) | +88% | −50% to +88% |

Two things drive the error.

**The TDP is not the real power ceiling.** CodeCarbon assumes a CPU at 100% load
draws its full rated TDP. On the dual E5-2620 v3, the database TDP implies 170 W
for the pair, while RAPL reported about 117 W at full load — the chips are held
near their base frequency and never reach the rated figure. On the EPYC 8024P
the gap is larger still.

**The assumed load-to-power curve does not match the real one.** In machine
mode CodeCarbon applies a cubic curve with a 10%-of-TDP floor
(`hardware.py:287-288`); in process mode it interpolates linearly from zero
(`hardware.py:346`). Neither shape is fitted to hardware. Real curves are convex
on some parts
(the E3-1240 v2 stays under 10 W up to 40% load, so the linear estimate
overshoots it by well over 100%) and saturate early on others (the Threadripper
reaches its power ceiling around 65% load, so the estimate *undershoots* at mid
load).

The practical reading: the fallback gets the order of magnitude right and can be
off by a factor of two in either direction on a specific machine and workload.
It is not a substitute for RAPL. If your numbers need to be defensible,
[enable RAPL](../how-to/enable-rapl.md).

### Wall-socket comparison

The Threadripper sweeps also record whole-machine power from a smart plug
(`tapo_power` in the CSV files). Those figures are not directly comparable to
the CPU numbers — they include the GPU, disks, fans and power supply losses, and
the machine drew about 115 W at idle. They are published for completeness, not as
a validation of the CPU figures.

A proper wall-socket validation — a controlled comparison of a wattmeter against
CodeCarbon's reported energy for the same interval, on the same machine — has
not been done. It is the reference method reviewers ask about, and no amount of
RAPL-versus-estimate analysis substitutes for it, because RAPL is itself an
instrument with its own error. Contributions are welcome.

## Where the error comes from

Three independent error sources compound. Which one dominates depends on your
setup, and the remedy differs for each.

**Power measurement.** Covered by the table above. Small when hardware counters
are available, potentially a factor of two when the TDP fallback is in use.

**Carbon intensity.** Often the largest term. When CodeCarbon has no data for
your country it falls back to a world average of 475 gCO₂eq/kWh. Real national
intensities span from under 50 gCO₂eq/kWh to over 700, so this default can be
wrong by close to an order of magnitude. Marginal versus average intensity, and
hourly versus annual averages, add further uncertainty that CodeCarbon does not
model. See [Methodology](methodology.md) for the data sources.

**Temporal resolution.** CodeCarbon samples every `measure_power_secs` seconds
(default 15). Energy counters accumulate between samples, so this does not lose
energy on the counter paths; but on the estimation path, and for workloads
shorter or spikier than the interval, the sampled load is a poor summary of what
actually happened.

## What to do about it

In rough order of impact:

1. **Enable RAPL on Linux** — see [Improve measurement accuracy with
   RAPL](../how-to/enable-rapl.md). This is the single largest improvement
   available on most machines, and it moves you from estimation to measurement.
2. **Set your country, region and cloud provider correctly** in the
   [configuration](../how-to/configuration.md). A wrong region is usually a
   larger error than a wrong power reading.
3. **Set `pue`** if you run in a datacenter whose overhead you know.
4. **Contribute your CPU model** to
   `codecarbon/data/hardware/cpu_power.csv` if CodeCarbon logs that it does not
   know your CPU. That moves you off the default-watts-per-thread path.
5. **Measure longer runs.** Short runs are dominated by sampling noise and
   tracker startup.
6. **Compare within one machine, not across machines.** Relative comparisons
   (this model versus that model, on the same hardware and backend) are far more
   trustworthy than absolute totals.

## Reproduce this yourself

Nothing here needs to be taken on trust.

- `examples/compare_cpu_load_and_RAPL.py` — runs the load sweep and writes a CSV
  with RAPL and estimated power side by side. Requires `stress-ng` and readable
  RAPL counters.
- `examples/compare_cpu_load_and_RAPL.ipynb` — plots the CSVs, including the
  sweeps committed under `codecarbon/data/hardware/cpu_load_profiling/`.
- `examples/rapl/` — diagnostic scripts for inspecting RAPL domains
  (`intel_rapl_show.py`, `test_rapl_domains.py`, `test_dram_option.py` and
  others).
- `examples/test_rapl_calculus.sh` — a shell check of the RAPL energy
  calculation.
- `examples/print_hardware.py` — shows which backend CodeCarbon selected on your
  machine, which tells you which row of the table above applies to you.

If you run the sweep on a CPU that is not yet profiled, a pull request adding
the CSV to `codecarbon/data/hardware/cpu_load_profiling/` is a directly useful
contribution.

## Known gaps

Stated plainly, because a validation page that only lists strengths is not a
validation page:

- No external wattmeter validation of any backend.
- GPU and RAM backends are not validated against an independent reference.
- The RAPL-versus-estimate comparison covers four CPUs, all Linux, none of them
  recent.
- No uncertainty interval is attached to reported emissions figures.
- On the dual E5-2620 v3, RAPL reported markedly lower package power when the
  same total load was spread over fewer cores than over all cores. The notebook
  flags this as unexpected and unexplained; it was reproduced on a second run.

<!-- Backend table and profiling figures last verified against the repository on 2026-08-12. -->
