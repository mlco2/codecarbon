# Output

## Choosing output methods

Use the `output_methods` parameter to select where emissions data is sent. It takes
a list of `OutputMethod` enum values:

```python-skip
from codecarbon import EmissionsTracker, OutputMethod

tracker = EmissionsTracker(
    output_methods=[OutputMethod.CSV, OutputMethod.API],
)
```

Available values: `CSV`, `API`, `LOGGER`, `PROMETHEUS`, `LOGFIRE`, `BOAMPS`, `SCI`.
It can also be set in the config file as a comma-separated string, e.g.
`output_methods=csv,api`. HTTP output is enabled separately via the
`emissions_endpoint` parameter.

!!! warning "Deprecation"
    The individual `save_to_file`, `save_to_api`, `save_to_logger`,
    `save_to_prometheus` and `save_to_logfire` parameters are deprecated and will be
    removed in a future version. Use `output_methods` instead. When `output_methods`
    is provided, the `save_to_*` flags are ignored. See the
    [deprecations list](https://docs.codecarbon.io/latest/reference/deprecations/).

## CSV

The package has an in-built logger that logs data into a CSV file named `emissions.csv` in the `output_dir`, provided as an input parameter (defaults to the current directory), for each experiment tracked across projects.

The columns are written in the field order of the `EmissionsData` dataclass
(`codecarbon/output_methods/emissions_data.py`).

The **Provenance** column says where each number comes from: a hardware counter, a model,
or configuration.

| Field | Description | Provenance |
|-------|-------------|------------|
| timestamp | Time of the experiment in `%Y-%m-%dT%H:%M:%S` format | |
| project_name | Name of the project, defaults to `codecarbon` | Config |
| run_id | ID of the run | Generated (UUID) |
| experiment_id | ID of the experiment the run belongs to, used by the API | Config |
| duration | Duration of the compute, in seconds | Measured (wall clock) |
| emissions | Emissions as CO₂-equivalents (CO₂eq), in kg | Computed: `energy × carbon intensity`, see the carbon intensity note |
| emissions_rate | Emissions divided per duration, in Kg/s | Computed: `emissions / duration` |
| cpu_power | Mean CPU power (W) | Varies by backend, see the CPU backends note. Mean of the per-interval samples, PUE-scaled |
| gpu_power | Mean GPU power (W) | Derived from the GPU energy-counter delta over each interval, then averaged. PUE-scaled |
| ram_power | Mean RAM power (W) | Modelled except on a Raspberry Pi 5, see the RAM note. PUE-scaled |
| cpu_energy | Energy used per CPU (kWh) | Same backend as `cpu_power`, PUE-inflated |
| gpu_energy | Energy used per GPU (kWh) | Accumulated board-energy counter: NVML `nvmlDeviceGetTotalEnergyConsumption` (`core/gpu_nvidia.py`) or AMD `amdsmi_get_energy_count` (`core/gpu_amd.py`); while the counter cannot be read, the power sampled every second × time. PUE-inflated |
| ram_energy | Energy used per RAM (kWh) | Modelled RAM power × interval, PUE-inflated |
| energy_consumed | Sum of cpu_energy, gpu_energy and ram_energy (kWh) | Sum of the three columns above; every term already PUE-inflated |
| water_consumed | Water footprint of the run, in litres | Computed: `wue × energy_consumed`. `0` unless you set `wue` |
| country_name | Name of the country where the infrastructure is hosted | IP geolocation (geojs, ipinfo.io fallback), or config in offline mode |
| country_iso_code | 3-letter alphabet ISO Code of the respective country | As `country_name` |
| region | Province/State/City where the compute infrastructure is hosted | As `country_name`; on cloud, from the cloud region lookup |
| cloud_provider | One of aws/azure/gcp | Cloud instance metadata probe |
| cloud_region | Geographical region (e.g., us-east-2 for aws, brazilsouth for azure, asia-east1 for gcp) | Cloud instance metadata probe |
| os | Operating system (e.g., Windows-10-10.0.19044-SP0) | |
| python_version | Python version (e.g., 3.8.10) | |
| codecarbon_version | Version of codecarbon used | |
| cpu_count | Number of CPUs | `psutil.cpu_count()`: logical threads, not physical cores. Under SLURM, the CPUs allocated to the job (`count_cpus` in `core/util.py`) |
| cpu_model | Example: Intel(R) Core(TM) i7-1065G7 CPU @ 1.30GHz | CPU model string detected at startup |
| gpu_count | Number of GPUs | NVML / AMDSMI device enumeration |
| gpu_model | Example: 1 x NVIDIA GeForce GTX 1080 Ti | NVML / AMDSMI device name |
| longitude | Longitude of the machine | IP geolocation, full precision, see the coordinates note |
| latitude | Latitude of the machine | IP geolocation, full precision, see the coordinates note |
| ram_total_size | Total RAM available (GB) | `psutil.virtual_memory().total` |
| tracking_mode | `machine` or `process` (default: `machine`) | Config |
| cpu_utilization_percent | Average CPU utilization during tracking period (%) | Mean of `psutil.cpu_percent()` samples, taken every second |
| gpu_utilization_percent | Average GPU utilization during tracking period (%) | Mean of NVML / AMDSMI utilization samples, taken every second |
| ram_utilization_percent | Average RAM utilization during tracking period (%) | Mean of `psutil.virtual_memory().percent` samples |
| ram_used_gb | Average RAM used during tracking period (GB) | Mean of `psutil.virtual_memory().used` samples |
| on_cloud | `Y` if on cloud, `N` for private infrastructure | Cloud instance metadata probe (`core/cloud.py`) |
| pue | Power Usage Effectiveness applied to this run (default `1.0`) | Config, see the PUE note |
| wue | Water Usage Effectiveness in L/kWh (default `0`) | Config |

### Notes on provenance

#### CPU backends

`cpu_power` and `cpu_energy` depend entirely on the backend selected at startup. The
backend is chosen once, logged at startup, and not recorded in the CSV. Roughly in
decreasing order of trustworthiness:

| Backend | Nature | Where |
|---|---|---|
| Intel RAPL (Linux) | Measured, hardware energy counter | `core/rapl.py` |
| Raspberry Pi 5 | Measured, PMIC voltage and current readings | `Raspberry` in `external/hardware.py` |
| Windows EMI | Measured, hardware energy counter | `core/windows_emi.py` |
| `powermetrics` (macOS, needs sudo) | Measured, OS-reported power. Effectively unreachable on Apple Silicon: `psutil` is a hard dependency, so the `cpu_load` path is selected first (`_try_platform_cpu_backend` in `core/resource_tracker.py`) | `core/powermetrics.py` |
| `cpu_load` mode | Modelled: cubic in load with a 10 % TDP floor in `machine` mode, linear `TDP × load/cpu_count` in `process` mode | `CPU._get_power_from_cpu_load` in `external/hardware.py` |
| `constant` mode | Modelled: `TDP × 0.5`, a flat 50 % of TDP | `CPU._get_power_from_cpus` in `external/hardware.py` |

The last two are estimates, and on a lightly loaded or unusual machine they can be far
from the truth. The selection order, including which options override which, is on the
[methodology page](../explanation/methodology.md); measured deviation figures are in
[accuracy](../explanation/accuracy.md).

#### RAM

`ram_power` and `ram_energy` are measured only on a Raspberry Pi 5, whose PMIC reports the
DRAM rails. Elsewhere, commodity hardware exposes no RAM energy counter, so CodeCarbon
estimates a DIMM count from the total RAM size, then applies 5 W per
DIMM on x86 (1.5 W on ARM), with decreasing marginal power above four DIMMs and a floor of
two DIMMs' worth (`RAM._calculate_ram_power` in `external/ram.py`). Treat these columns as an order-of-magnitude
heuristic. If you can measure your own RAM power, override it with `force_ram_power`.

#### Carbon intensity

`emissions` is only as good as the carbon intensity behind it, which comes from a fallback
chain documented on the [methodology page](../explanation/methodology.md). No column
records which level answered: check the run's log output if you need to know.

#### PUE

PUE multiplies the per-component energy and power columns, not just the total. In
`_do_measurements` (`emissions_tracker.py`) the PUE is applied to each hardware measurement
before it is accumulated. With `pue=1.5`, the `cpu_energy` column is therefore 1.5x the
energy the CPU actually drew: it is datacenter energy attributed to the CPU, not raw CPU
energy. The power columns are scaled the same way, see the note below.
`water_consumed` is computed from the already-inflated energy.

#### Coordinates

`latitude` and `longitude` are written at full precision in the CSV. Rounding to one
decimal (~11 km) is applied only when data is sent to the CodeCarbon API
(`core/api_client.py`). If the CSV leaves your machine, treat the coordinates as
precise.

!!! note "PUE and the power columns"
    Since v3.3.1, the `pue` multiplier is applied to the reported power columns
    (`cpu_power`, `gpu_power`, `ram_power`) as well as to the energy columns, so
    that `energy_consumed` stays reconstructible from the reported power. Before
    that, only the energy was scaled. With `pue=1.5`, a machine measured at 100 W
    is reported as 150 W, and that also applies to forced values: `force_cpu_power=100`
    with `pue=1.5` reports a 150 W CPU. This is intended: the columns describe the
    power drawn at the facility level, not at the socket.

!!! note
    Developers can enhance the Output interface by implementing a custom class that extends `BaseOutput` at `codecarbon/output.py`. For example, to log into a database.

## Prometheus

[Prometheus](https://github.com/prometheus/prometheus) is a systems and service monitoring system. It collects metrics from configured targets at given intervals, evaluates rule expressions, displays the results, and can trigger alerts when specified conditions are observed.

CodeCarbon exposes all its metrics with the suffix `codecarbon_`.

Current version uses pushgateway mode. If your pushgateway server needs auth, set your environment variables `PROMETHEUS_USERNAME` and `PROMETHEUS_PASSWORD` so CodeCarbon can push the metrics.

### How to test locally

Deploy a local version of Prometheus + Prometheus Pushgateway:

```bash
docker-compose up
```

Run your EmissionsTracker as usual, with `save_to_prometheus=True`:

```python-skip
from codecarbon import OfflineEmissionsTracker

tracker = OfflineEmissionsTracker(
    project_name="my_project",
    country_iso_code="USA",
    save_to_prometheus=True,
)
tracker.start()
# Your code here
tracker.stop()
```

Go to [localhost:9090](http://localhost:9090). Search for `codecarbon_` to see all metrics.

## Logfire

[Logfire](https://docs.pydantic.dev/logfire/) is an observability platform.

CodeCarbon exposes all its metrics with the suffix `codecarbon_`.

### How to use it

Run your EmissionsTracker as usual, with `save_to_logfire=True`:

```python-skip
from codecarbon import OfflineEmissionsTracker

tracker = OfflineEmissionsTracker(
    project_name="my_project",
    country_iso_code="USA",
    save_to_logfire=True,
)
tracker.start()
# Your code here
tracker.stop()
```

The first time it will ask you to log in to Logfire. Once you log in and set the default Logfire project, the metrics will appear following the format `codecarbon_*`.

## BoAmps

[BoAmps](https://github.com/Boavizta/BoAmps) is a standardized JSON format for reporting AI and ML energy consumption.

### How to use it

Run your EmissionsTracker as usual, adding `OutputMethod.BOAMPS` to `output_methods`:

```python-skip
from codecarbon import OfflineEmissionsTracker, OutputMethod

tracker = OfflineEmissionsTracker(
    project_name="my_project",
    country_iso_code="USA",
    output_methods=[OutputMethod.CSV, OutputMethod.BOAMPS],
)
tracker.start()
# Your code here
tracker.stop()
```

CodeCarbon writes a final report named `boamps_report_<run_id>.json` in `output_dir`.

If you need to enrich the report with task metadata, datasets, or publisher information,
use the generic `metadata` parameter and put the BoAmps context under the `boamps` key:

```python-skip
from codecarbon import OfflineEmissionsTracker, OutputMethoddocs/reference/output.md

tracker = OfflineEmissionsTracker(
  project_name="my_project",
  country_iso_code="USA",
  output_methods=[OutputMethod.BOAMPS],
  metadata={
    "boamps": {
      "task": {
        "taskStage": "training",
        "taskFamily": "classification",
        "algorithms": ["random_forest"],
        "dataset": "my_dataset",
      },
      "quality": "medium",
    },
    "my_other_metadata": {"owner": "ml-team"},
  },
)
tracker.start()
# Your code here
tracker.stop()
```

`metadata` can also be a path to a JSON file (`metadata="metadata.json"`).
For backward compatibility, if `metadata` is a dict without a `boamps` key,
the full dict is interpreted as BoAmps metadata.

Sample output:
```json
{
  "header": {
    "formatVersion": "0.1",
    "formatVersionSpecificationUri": "https://github.com/Boavizta/BoAmps/tree/main/model",
    "reportId": "79e4408f-ec31-476f-a2c5-8ca7f53e6cc7",
    "reportDatetime": "2026-04-09 23:07:42"
  },
  "measures": [
    {
      "measurementMethod": "codecarbon",
      "version": "3.2.6",
      "averageUtilizationCpu": 0.6,
      "powerConsumption": 6.515418096322266e-05,
      "measurementDuration": 7.052794550996623,
      "measurementDateTime": "2026-04-09 23:07:42"
    }
  ],
  "system": {
    "os": "Linux-6.17.0-19-generic-x86_64-with-glibc2.42"
  },
  "software": {
    "language": "python",
    "version": "3.12.12"
  },
  "infrastructure": {
    "infraType": "onPremise",
    "components": [
      {
        "componentName": "Intel(R) Core(TM) Ultra 7 265H",
        "componentType": "cpu",
        "nbComponent": 8
      },
      {
        "componentType": "ram",
        "nbComponent": 1,
        "memorySize": 30.052967071533203
      }
    ]
  },
  "environment": {
    "country": "France",
    "latitude": 48.6,
    "longitude": 2.3
  }
}
```

## HTTP Output

The HTTP Output allows calling a webhook with emission data when the tracker is stopped. Use the `emissions_endpoint` parameter to specify your endpoint.

## CodeCarbon API

You can send all your data to the CodeCarbon API so you have your historical data in one place. By default, nothing is sent to the API. Use `save_to_api=True` and configure your API credentials.

## Logger Output

See [Collecting emissions to a logger](../how-to/logging.md).

## SCI

The [Software Carbon Intensity](https://sci.greensoftware.foundation/) specification, standardised as ISO/IEC 21031:2024, expresses a workload's footprint as a rate:

```
SCI = (E * I + M) / R
```

CodeCarbon measures `E` (energy consumed, kWh) and applies `I` (carbon intensity, gCO2eq/kWh). `R` and `M` are declarations:

- `R`, the functional unit: one request, one training run, 1k tokens. There is no default, so if you do not declare one the report is still written, with `sci: null` and a `status` field saying why.
- `M`, the embodied emissions attributable to the run. When you do not declare a figure the report says `"M_source": "not declared"`, so a reader can see the report is a partial one.

### How to use it

Enable the output method and put the declarations under the `sci` key of the generic `metadata` parameter, next to any other output's section (for example `boamps`):

```python
tracker = EmissionsTracker(
    output_methods=["csv", "sci"],
    metadata={
        "sci": {
            "functionalUnit": {"name": "inference request", "count": 10000},
            "embodied": {"gCO2e": 42.5, "source": "manufacturer LCA, 4y amortization"},
            "reporter": {"organization": "Acme", "contact": "green@acme.example"},
            "boundary": "Application only; excludes client devices and network.",
        }
    },
)
```

`metadata` can also be a path to a JSON file, which is how to set it from `.codecarbon.config`:

```ini
[codecarbon]
output_methods = csv,sci
metadata = ./metadata.json
```

A relative `metadata` path is resolved against the current working directory, not the config file's location. The file holds the same `sci` section:

```json
{
  "sci": {
    "functionalUnit": {"name": "inference request", "count": 10000},
    "embodied": {"gCO2e": 42.5, "source": "manufacturer LCA, 4y amortization"},
    "reporter": {"organization": "Acme", "contact": "green@acme.example"},
    "boundary": "Application only; excludes client devices and network."
  }
}
```

If `metadata` has no `sci` section, or it cannot be read, the report is still written without the declarations. To load a file holding only the SCI declarations (no `sci` wrapper) when you build the handler yourself, use `SCIOutput.from_file(path)`; `SCIOutput.from_dict(section)` does the same from a dict.

Both `gCO2e` and `gco2e` are accepted for the embodied figure.

!!! warning "The configuration-only path needs a count in the context file"
    `set_functional_unit_count()` needs a reference to the handler, and the handler created by `output_methods = csv,sci` is owned by the tracker. So with configuration alone, `sci` is `null` in every report unless `functionalUnit.count` is hardcoded in the `sci` section of `metadata`. If the count is only known at the end of the run, construct `SCIOutput` yourself and pass it via `output_handlers=[...]`.

CodeCarbon writes a final report named `sci_report_<run_id>.json` in `output_dir`, plus `sci_report_tasks_<run_id>.json` when tasks are used. A report written by `tracker.flush()` is interim: it applies the full declared `M` to the energy measured so far, so its `sci` is higher than the final one, and it is overwritten by the report written at `stop()`. In the task report, `M` is apportioned across tasks by their share of the tasks' summed duration: the declared `M` is the embodied carbon of the device for the whole run, so giving each task the full figure would count it once per task. If the tasks do not cover the whole run, the full `M` is still spread over the tasks alone. Task reports show `"pue": null` because task data does not carry the PUE. `R` is not apportioned, because CodeCarbon cannot know how many functional units fell inside a task, so each task reports `sciShare`, its share of the run-level SCI, instead of `sci`. `I` is derived as `emissions * 1000 / energy_consumed` rather than recomputed, so the report is consistent with the CSV by construction; the PUE that was applied is recorded separately in the provenance block.

Sample output:
```json
{
  "specVersion": "ISO/IEC 21031:2024",
  "generatedBy": "codecarbon 3.2.6",
  "runId": "79e4408f-ec31-476f-a2c5-8ca7f53e6cc7",
  "projectName": "my_project",
  "timestamp": "2025-01-15T10:30:00",
  "sci": 0.00845,
  "unit": "gCO2eq per inference request",
  "terms": {
    "E_kWh": 0.1007,
    "I_gCO2e_per_kWh": 417.08,
    "M_gCO2e": 42.5,
    "R": 10000,
    "R_name": "inference request"
  },
  "provenance": {
    "I_source": "codecarbon regional intensity, country_iso_code=FRA",
    "M_source": "manufacturer LCA, 4y amortization",
    "measurementBoundary": "Application only; excludes client devices and network.",
    "durationSeconds": 3600.0,
    "hardware": {"cpu": "Intel Xeon", "gpu": "NVIDIA A100", "ramTotalGB": 64.0},
    "pue": 1
  }
}
```

See [examples/sci_output.py](https://github.com/mlco2/codecarbon/blob/master/examples/sci_output.py) for a runnable example, including the context file format and how to declare the functional unit count from Python.
