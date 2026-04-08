# When to use CodeCarbon

CodeCarbon tracks carbon emissions from **local computing**—code that runs on hardware you control.

## Use CodeCarbon when you

- **Train models** on your machine, server, or cloud VM
- **Run inference** on your own hardware (laptop, GPU server, on-prem)
- **Execute any code** that consumes electricity on infrastructure you control

CodeCarbon measures actual power consumption (CPU, GPU, RAM) and converts it to CO₂ emissions using grid carbon intensity.

## Use EcoLogits when you

- **Call GenAI APIs** (OpenAI, Anthropic, Mistral, Hugging Face, etc.)
- **Don't control the hardware**—the model runs on the provider's infrastructure
- **Want to estimate** the environmental impact of API requests from request metadata

[EcoLogits](https://ecologits.ai/latest/?utm_source=codecarbon&utm_medium=docs) estimates impacts from API calls without access to the underlying hardware.

## Both are complementary

Use CodeCarbon for training and local inference. Use EcoLogits for remote API inference. Together they cover the full lifecycle of AI workloads.
