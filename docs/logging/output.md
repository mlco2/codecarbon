# Output

The output method defines how emissions data is saved or transmitted.

## Output Methods

### 1. Console Output

By default, CodeCarbon prints emissions to the console:

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker()
tracker.start()
# Your code here
emissions = tracker.stop()
```

### 2. File Output

Save emissions to a CSV or JSON file:

```python
tracker = EmissionsTracker(save_to_file=True, output_dir="./emissions")
```

### 3. HTTP Output

Send emissions to an HTTP endpoint:

```python
tracker = EmissionsTracker(
    emissions_endpoint="http://your-endpoint.com/emissions"
)
```

### 4. Prometheus

Export metrics to Prometheus:

```python
tracker = EmissionsTracker(prometheus_endpoint="http://localhost:8008")
```

### 5. CodeCarbon API

Send emissions to the CodeCarbon cloud API (requires login):

```python
tracker = EmissionsTracker(save_to_api=True)
```

### 6. Logfire

Send emissions to Logfire observability platform:

```python
tracker = EmissionsTracker(save_to_logfire=True)
```

## Output Fields

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
| cloud_region | Geographical region (e.g., us-east-2 for aws) |
| os | Operating system (e.g., Windows-10-10.0.19044-SP0) |
| python_version | Python version (e.g., 3.8.10) |
| codecarbon_version | Version of codecarbon used |

## Examples

See the [Examples](../getting-started/examples.md) page for detailed usage.
