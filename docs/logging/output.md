# Output

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

```python
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

```python
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

## HTTP Output

The HTTP Output allows calling a webhook with emission data when the tracker is stopped. Use the `emissions_endpoint` parameter to specify your endpoint.

## CodeCarbon API

You can send all your data to the CodeCarbon API so you have your historical data in one place. By default, nothing is sent to the API. Use `save_to_api=True` and configure your API credentials.

## Logger Output

See [Collecting emissions to a logger](to_logger.md).
