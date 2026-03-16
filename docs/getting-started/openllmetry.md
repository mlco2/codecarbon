# OpenLlmety Integration {#openllmetry}

CodeCarbon can be integrated with [OpenLlmety](https://github.com/traceloop/openllmetry) for observability and tracing of LLM applications. This integration allows you to track carbon emissions alongside your LLM metrics in platforms like LangSmith, LangFuse, or any OpenTelemetry-compatible backend.

![OpenLlmety Overview](https://github.com/traceloop/openllmetry/raw/main/docs/public/openllmetry-logo.png){.align-center width="400px"}

## What is OpenLlmety?

OpenLlmety is an open-source observability platform for LLM applications. It provides:
- Automatic instrumentation for LLM frameworks (LangChain, OpenAI, etc.)
- Integration with multiple backends (LangSmith, LangFuse, etc.)
- OpenTelemetry-based tracing with custom attributes

## Installation

First, install the OpenLlmety extra dependency:

```bash
pip install codecarbon[openllmetry]
```

Or install OpenLlmety directly:

```bash
pip install openllmetry
```

## Quick Start

### Method 1: Environment Variable

Set the `CODECARBON_OPENLLMETRY` environment variable to enable the integration:

```bash
export CODECARBON_OPENLLMETRY=true
```

Then use CodeCarbon normally:

```python
from codecarbon import EmissionsTracker

with EmissionsTracker() as tracker:
    # Your LLM code here
    result = llm.invoke("Hello world")
```

### Method 2: Programmatic Enable

Enable OpenLlmety integration in your code:

```python
from codecarbon import enable_openllmetry, EmissionsTracker

# Enable OpenLlmety integration
enable_openllmetry()

# Then use CodeCarbon normally
with EmissionsTracker() as tracker:
    # Your LLM code here
    result = llm.invoke("Hello world")
```

### Method 3: EmissionsTracker Parameter

Use the `save_to_openllmetry` parameter:

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(save_to_openllmetry=True)
tracker.start()

# Your LLM code here

tracker.stop()
```

## Using with LangFuse

To use with LangFuse, set up your environment and initialize both integrations:

```python
from langfuse import Langfuse
from openllmetry import trace
from codecarbon import enable_openllmetry, EmissionsTracker

# Initialize LangFuse
langfuse = Langfuse()

# Initialize OpenLlmety to export to LangFuse
trace(langfuse)

# Enable CodeCarbon OpenLlmety integration
enable_openllmetry()

# Track emissions alongside your LLM calls
with EmissionsTracker() as tracker:
    response = llm.invoke("What is the capital of France?")
    # Emissions data will appear in LangFuse as attributes
```

## Using with LangSmith

Similarly, for LangSmith:

```python
from langsmith import Client
from openllmetry import trace
from codecarbon import enable_openllmetry, EmissionsTracker

# Initialize LangSmith
client = Client()

# Initialize OpenLlmety to export to LangSmith
trace(client)

# Enable CodeCarbon OpenLlmety integration
enable_openllmetry()

# Track emissions alongside your LLM calls
with EmissionsTracker() as tracker:
    response = llm.invoke("Hello world")
    # Emissions data will appear in LangSmith traces
```

## Emissions Data in Traces

When enabled, CodeCarbon adds the following attributes to OpenTelemetry spans:

| Attribute | Description |
|----------|-------------|
| `codecarbon.emissions_kg` | Total CO2 emissions in kilograms |
| `codecarbon.energy_consumed_kwh` | Total energy consumed in kWh |
| `codecarbon.duration_seconds` | Duration of the tracking period |
| `codecarbon.emissions_rate_kg_per_sec` | Emissions rate in kg/s |
| `codecarbon.cpu_power_watts` | Average CPU power in watts |
| `codecarbon.gpu_power_watts` | Average GPU power in watts |
| `codecarbon.ram_power_watts` | Average RAM power in watts |
| `codecarbon.country` | Country where the code is running |
| `codecarbon.region` | Region within the country |
| `codecarbon.cloud_provider` | Cloud provider (if applicable) |
| `codecarbon.cloud_region` | Cloud region (if applicable) |

## Configuration

### Environment Variables

- `CODECARBON_OPENLLMETRY=true` - Enable the OpenLlmety integration

### Programmatic Options

```python
from codecarbon import enable_openllmetry

# With custom service name
enable_openllmetry(service_name="my-llm-service")
```

## Deprecation Notice

The Comet.ml integration is deprecated. Please use the OpenLlmety integration instead. The Comet integration will be removed in a future version of CodeCarbon.

For more information about OpenLlmety, visit: https://github.com/traceloop/openllmetry
