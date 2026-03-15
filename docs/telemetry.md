# Telemetry

CodeCarbon collects anonymous usage data to help improve the library. This page explains what we collect, how we handle your data, and how you can control it.

## Telemetry Tiers

CodeCarbon supports three telemetry levels:

| Tier | Env Variable | Description |
|------|-------------|-------------|
| Off | `CODECARBON_TELEMETRY=off` | No telemetry collected |
| Internal | `CODECARBON_TELEMETRY=internal` | Private usage data (helps us improve CodeCarbon) |
| Public | `CODECARBON_TELEMETRY=public` | Full telemetry including emissions (shared on public leaderboard) |

## What We Collect

### Internal (Private)

When you enable Internal telemetry, we collect:

- **Environment**: Python version, OS, CodeCarbon version, installation method
- **Hardware**: CPU model/count, GPU model/count, RAM, CUDA version
- **Usage Patterns**: Tracking mode, output methods configured, hardware tracked
- **ML Ecosystem**: Detected frameworks (PyTorch, TensorFlow, Transformers, etc.)
- **Context**: Notebook environment, CI/CD detection, container runtime
- **Performance**: Hardware detection success, RAPL availability, errors

### Public (Leaderboard)

When you enable Public telemetry, everything above **plus**:

- **Emissions Data**: Total CO2 emissions, energy consumed, duration
- **Utilization**: CPU, GPU, RAM utilization averages

This data is shared publicly on the CodeCarbon leaderboard to encourage green computing practices.

## Privacy

We're committed to protecting your privacy:

- **No PII**: We don't collect personally identifiable information
- **Anonymized**: Machine identifiers are hashed
- **GPS Precision**: Geographic coordinates are rounded to ~10km
- **GDPR Compliant**: We support opt-in consent and data deletion requests
- **Minimal Data**: We only collect what's needed to improve the library

## Configuration

### Environment Variables

```bash
# Set telemetry tier
export CODECARBON_TELEMETRY=internal

# Set custom OTEL endpoint (optional)
export CODECARBON_OTEL_ENDPOINT=https://your-otel-endpoint.com/v1/traces
```

### In Code

```python
from codecarbon import EmissionsTracker

# Telemetry can also be set in the tracker
tracker = EmissionsTracker(
    project_name="my-project",
    telemetry="internal"  # or "public" or "off"
)
```

## First-Run Prompt

On first run, CodeCarbon will prompt you to choose your telemetry level if:

- No `CODECARBON_TELEMETRY` environment variable is set
- No previous preference was saved

You can skip the prompt by setting the environment variable before running CodeCarbon.

## Disabling Telemetry

To completely disable telemetry:

```bash
export CODECARBON_TELEMETRY=off
```

Or in your code:

```python
tracker = EmissionsTracker(telemetry="off")
```

## OTEL Integration

Telemetry data is sent via OpenTelemetry (OTEL). To use your own OTEL collector:

```bash
export CODECARBON_OTEL_ENDPOINT=https://your-collector:4318/v1/traces
```

Install the OTEL extras if you want to export telemetry:

```bash
pip install codecarbon[telemetry]
```

## Data Retention

- Internal telemetry: Retained for 12 months
- Public leaderboard data: Displayed indefinitely
- You can request data deletion by contacting the CodeCarbon team
