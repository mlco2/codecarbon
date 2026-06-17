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

Available values: `CSV`, `API`, `LOGGER`, `PROMETHEUS`, `LOGFIRE`, `BOAMPS`.
It can also be set in the config file as a comma-separated string, e.g.
`output_methods=csv,api`. HTTP output is enabled separately via the
`emissions_endpoint` parameter.

!!! warning "Deprecation"
    The individual `save_to_file`, `save_to_api`, `save_to_logger`,
    `save_to_prometheus` and `save_to_logfire` parameters are deprecated and will be
    removed in a future version. Use `output_methods` instead. When `output_methods`
    is provided, the `save_to_*` flags are ignored.

## CSV

The package has an in-built logger that logs data into a CSV file named `emissions.csv` in the `output_dir`, provided as an input parameter (defaults to the current directory), for each experiment tracked across projects.

| Field | Description |
|-------|-------------|
| timestamp | Time of the experiment in `%Y-%m-%dT%H:%M:%S` format |
| project_name | Name of the project, defaults to `codecarbon` |
| run_id | ID of the run |
| duration | Duration of the compute, in seconds |
| emissions | Emissions as CO₂-equivalents (CO₂eq), in kg |
| emissions_rate | Emissions divided per duration, in Kg/s |
| cpu_power | Mean CPU power (W) |
| gpu_power | Mean GPU power (W) |
| ram_power | Mean RAM power (W) |
| cpu_energy | Energy used per CPU (kWh) |
| gpu_energy | Energy used per GPU (kWh) |
| ram_energy | Energy used per RAM (kWh) |
| energy_consumed | Sum of cpu_energy, gpu_energy and ram_energy (kWh) |
| country_name | Name of the country where the infrastructure is hosted |
| country_iso_code | 3-letter alphabet ISO Code of the respective country |
| region | Province/State/City where the compute infrastructure is hosted |
| on_cloud | `Y` if on cloud, `N` for private infrastructure |
| cloud_provider | One of aws/azure/gcp |
| cloud_region | Geographical region (e.g., us-east-2 for aws, brazilsouth for azure, asia-east1 for gcp) |
| os | Operating system (e.g., Windows-10-10.0.19044-SP0) |
| python_version | Python version (e.g., 3.8.10) |
| codecarbon_version | Version of codecarbon used |
| cpu_count | Number of CPUs |
| cpu_model | Example: Intel(R) Core(TM) i7-1065G7 CPU @ 1.30GHz |
| gpu_count | Number of GPUs |
| gpu_model | Example: 1 x NVIDIA GeForce GTX 1080 Ti |
| longitude | Longitude, with reduced precision to a range of 11.1 km / 123 km² (privacy protection) |
| latitude | Latitude, with reduced precision to a range of 11.1 km / 123 km² (privacy protection) |
| ram_total_size | Total RAM available (GB) |
| tracking_mode | `machine` or `process` (default: `machine`) |
| cpu_utilization_percent | Average CPU utilization during tracking period (%) |
| gpu_utilization_percent | Average GPU utilization during tracking period (%) |
| ram_utilization_percent | Average RAM utilization during tracking period (%) |
| ram_used_gb | Average RAM used during tracking period (GB) |

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
