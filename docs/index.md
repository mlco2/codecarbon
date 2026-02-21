# CodeCarbon

![Banner](./_images/banner.png){: .align-center width="700px"}

---

## Welcome to CodeCarbon

CodeCarbon is a Python library that helps you track and reduce the carbon emissions from your computing tasks.

## Quick Links

| Section | Description |
|---------|-------------|
| [Installation](./installation/) | Get started with CodeCarbon |
| [Usage](./usage/) | Learn how to use CodeCarbon |
| [API Reference](./api/) | Full API documentation |
| [Examples](./examples/) | Example usage patterns |
| [Methodology](./methodology/) | How emissions are calculated |

## Features

- **Easy Integration** - Simple API to track emissions
- **Multiple Output Formats** - CSV, JSON, HTTP, Prometheus, Grafana
- **Hardware Support** - CPU, GPU, cloud provider detection
- **International** - Supports multiple countries and grid regions

## Installation

```bash
pip install codecarbon
```

## Quick Start

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker()
tracker.start()

# Your code here

emissions = tracker.stop()
print(f"Emissions: {emissions} kg CO2")
```

---

*For more details, see the [Usage Guide](./usage/).*
