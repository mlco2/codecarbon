# How CodeCarbon works

CodeCarbon samples the power drawn by your hardware, integrates it into energy
over the lifetime of your run, and multiplies that energy by the carbon
intensity of the grid supplying the machine.

That is the whole idea. This page is the mental model — enough to read your own
output and know what it means. When you need the exact backend, constant or
fallback that produced a given number, [Methodology](methodology.md) states each
one with the line of source it comes from.

## The formula

```text
emissions = Σ_intervals (power × Δt × PUE) × carbon_intensity
```

- **power** — watts drawn by the CPU, GPU and RAM at the moment of sampling.
- **Δt** — the sampling interval, `measure_power_secs`, 15 seconds by default.
  Power × Δt is energy; summing over every interval gives the energy of the run.
- **PUE** — power usage effectiveness, an optional multiplier for datacentre
  overhead such as cooling. It defaults to 1.0, meaning no overhead assumed.
- **carbon_intensity** — grams of CO₂-equivalent emitted per kilowatt-hour on
  the grid the machine draws from.

Everything else in the documentation is detail about how those four terms are
obtained.

## What is measured and what is modelled

This is the single most important thing to understand about a CodeCarbon
number, and the thing most likely to be assumed rather than checked.

| Component | On a good day | Otherwise |
|---|---|---|
| **CPU** | Measured. Hardware energy counters via RAPL on Linux, the Energy Meter Interface on Windows 11, or `powermetrics` on macOS. | **Modelled** from CPU load and a table lookup of your processor's TDP — or, if the model is unrecognised, a flat guess. |
| **RAM** | **Always modelled.** There is no RAM power counter on any supported platform. CodeCarbon guesses your DIMM count from total memory and assigns watts per DIMM. | — |
| **GPU** | Measured. Energy counters read directly from the device — NVML on Nvidia, AMDSMI on AMD. | Not counted. Without a supported GPU library there is no GPU estimate — the figure is simply absent. |

The consequence is worth stating outright: **the same column in the same CSV can
be a hardware reading on one machine and an educated guess on another.** A run
on a Linux box with readable RAPL files is measurement. The identical script on
a cloud VM without RAPL exposed produces a number of the same shape from a
model. Nothing in the output distinguishes them; the startup log names the CPU
backend that was selected.

Which of those two you got is the biggest driver of how far your number is from
reality — larger than the grid data, larger than the sampling interval, larger
than anything you can tune. [Accuracy and validation](accuracy.md) puts figures
on the gap.

The RAM estimate deserves its own caution. Its central constant — watts per
memory module — is asserted in the code with no source behind it, and on a
low-power machine RAM can be a large share of the total. If you know your real
configuration, override it with `force_ram_power`. The
[RAM section of the methodology](methodology.md#ram) gives the full step
function and the override recipe.

## Where the carbon intensity comes from

CodeCarbon resolves the grid figure through a six-level ladder, taking the first
level that answers: a value you forced explicitly, then a cloud provider and
region lookup, then a live reading from Electricity Maps if you have configured
a token, then a sub-national region for the handful of countries with regional
data, then a national average, and finally the 475 gCO₂eq/kWh world average.

The important property is that **the ladder degrades silently**. A cloud region
that is missing from the dataset falls back to the country; an unrecognised
country falls back to the world average. Nothing in the CSV, the API payload or
the emissions figure records which level answered — a live regional reading and
a global fallback produce output of identical shape. If provenance matters for
your use, check the startup logs or set the intensity explicitly. The
[carbon intensity section](methodology.md#carbon-intensity) lists each level,
its data source and its condition.

## What this page deliberately leaves out

Sampling is per-machine by default; `tracking_mode="process"` narrows CPU and
RAM attribution to your process, though never the GPU, which is always measured
device-wide. Disk, network and peripherals are outside the measurement boundary
entirely. Both of these change how a number should be read, and both are
covered in [Methodology](methodology.md).

## Where to go next

CodeCarbon is useful and its estimates are imperfect, and both of those are
true at the same time. The honest way to use it is to know which of the two you
are holding.

- **Evaluating whether to trust the tool?**
  [Methodology](methodology.md) is the full chain, constant by constant, with
  every fallback condition stated and every value traced to its source line.
- **Want to know how far off you are?**
  [Accuracy and validation](accuracy.md) reports measured deviations between
  the estimation path and hardware counters, plus the known gaps.
- **Want the largest single improvement available to you?**
  On Linux, make the RAPL counters readable. That converts your CPU number from
  a model into a measurement, and it is a one-time setup:
  [Enable RAPL](../how-to/enable-rapl.md).
- **Citing CodeCarbon in a paper or a report?**
  [References](references.md) holds the bibliography, including the primary
  literature on RAPL's own accuracy.
