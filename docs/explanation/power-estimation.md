# How Power Estimation Works in CodeCarbon

CodeCarbon tracks energy consumption by periodically querying the underlying hardware interfaces (e.g., RAPL for Intel CPUs, NVML for NVIDIA GPUs, AMDSMI for AMD GPUs) or by falling back on constant power models for non-supported hardware (such as generic CPU or RAM matching). 

While energy is the metric primarily responsible for CO₂ emissions estimations, tracking **power** (measured in Watts or kiloWatts) is equally important to provide meaningful dashboards and to help users understand their instantaneous consumption.

## 1. Energy as the Source of Truth

The most accurate tracking methods rely on built-in hardware energy counters rather than instantaneous power draw. For example:

- **NVIDIA GPUs** using `nvmlDeviceGetTotalEnergyConsumption` return accumulated energy in millijoules.
- **AMD GPUs** using `amdsmi_get_energy_count` yield a counter that is multiplied by its resolution and converted into millijoules.
- **CPUs** using the RAPL interface read from files like `energy_uj` to get accumulated microjoules.
- **RAM** using the RAPL interface read from files like `energy_uj` to get accumulated microjoules. See `rapl_include_dram` option. Not used by default. 

At every measurement interval, CodeCarbon calculates the `energy_delta` by subtracting the previously tracked `last_energy` from the current total energy reading.

## 2. Power Estimation from Energy Deltas

Instead of relying solely on instantaneous power sensors (which might not represent the whole interval due to microscopic spikes or drops between samples), CodeCarbon derives the average power over the latest measurement interval by backward-computing it from the total energy delta.

The `Power.from_energies_and_delay` method handles this operation:

```python
delta_energy_kwh = float(abs(energy_now.kWh - energy_previous.kWh))
power_kw = delta_energy_kwh / delay.hours
```

This conversion ensures that the computed power correctly reflects the true, steady average power usage across the whole measured time window (`delay`).

## 3. Emitting Hardware Metrics

The tracker has designated logic blocks for different components (e.g., CPU, RAM, GPU). Every `last_duration` seconds, each hardware component executes its `measure_power_and_energy()` method, taking the following steps for all monitored devices of that type:

1. Retrieves device-level stats (via a `delta` operation), updating `last_energy` for the next cycle.
2. Sums the total energy consumption safely into an aggregated Energy object.
3. Sums all derived power usage (`power_kw` from the delta) across the devices into a Total Power object.

## 4. Running Averages in the Main Emissions Tracker

Inside the main `EmissionsTracker`, the energy values are securely accumulated over the session's lifespan.

For recording the power, a running sum is maintained:

- As CodeCarbon sequentially takes measurements, it tracks the output of `power.W`.
- It dynamically increments running variables like `_gpu_power_sum`, `_cpu_power_sum`, `_ram_power_sum`.
- It increments a global counter `_power_measurement_count`.

At the end of an execution task (or when data is exported), the true average Power is formulated:
```python
avg_gpu_power = _gpu_power_sum / _power_measurement_count
```
This smoothing process prevents singular short measurement anomalies from skewing the final aggregated power values published in `EmissionsData`.

## Summary Pipeline

In short:

1. **Hardware Counters (Accumulated Energy)**
2. Subtract `last_energy` = **Energy Delta**
3. Divide Energy Delta by `last_duration` = **Interval Average Power**
4. Keep track of the sums of Interval Average Power
5. Divide by number of samples = **Global Average Power representation**.

## Challenges and Edge Cases

Because power is derived from the difference between two accumulating numbers and a time delta, several edge cases can lead to anomalies (like sudden values of millions of Watts):

### 1. Counter Wrapping and Resets
Hardware counters have maximum bounds (e.g., 32-bit or 64-bit integers). Once they reach their maximum limit, they wrap around to zero. If the current energy is less than the previous energy, a naive calculation would be negative. CodeCarbon must detect this and safely handle the overflow to prevent negative power outputs. Similarly, if the hardware resets or the driver reloads mid-run, the counter might abruptly restart from 0.

### 2. Micro-Intervals and Tiny Time Deltas
If two measurements happen too close together (due to thread scheduling anomalies, initial configuration, or rapid manual tracking calls), the time delta (`last_duration`) becomes extremely small. Dividing even a tiny, expected energy delta by an artificially small time slice can cause the derived Power (W) to explode into mathematically huge numbers (e.g., measuring 2.5 million Watts), even if the underlying counter merely shifted by a fraction of a Joule.

### 3. Multi-Chip Modules (MCM)
Modern hardware, such as AMD's MI250X GPUs, often places multiple compute dies (GCDs) on a single package. The driver might expose energy counters that behave differently than expected (e.g., counters resetting to zero, or different sensors polling at different intervals). Misaligning the tracking scope or reading uninitialized accumulators early in the run can lead to wildly skewed deltas that propagate into massive power spikes.

By relying heavily on energy accumulators rather than instantaneous power readings, CodeCarbon ensures a highly accurate sum of the total consumed energy. However, whenever you see an impossibly high "power" reading in the logs or emissions files, it is almost certainly a calculation artifact of dividing an unexpected energy delta by a time interval.
