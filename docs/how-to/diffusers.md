# Track Carbon Emissions with HuggingFace Diffusers

HuggingFace Diffusers is a library for generating images, audio, and 3D structures using diffusion models. CodeCarbon measures the carbon impact of running these generative models, helping you understand the environmental cost of image generation and other synthetic media tasks.

## Installation

```console
pip install codecarbon diffusers torch transformers
```

## Generating Images

Here's how to track the carbon emissions of image generation:

```python
# mktestdocs: skip
from diffusers import StableDiffusionPipeline
from codecarbon import EmissionsTracker

# Load the model
pipeline = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
pipeline = pipeline.to("cuda")

# Track image generation emissions
prompt = "A serene landscape with mountains and a lake at sunset"
with EmissionsTracker() as tracker:
    image = pipeline(prompt, num_inference_steps=50).images[0]

image.save("generated_image.png")
print(f"Image generation emissions: {tracker.final_emissions:.6f} kg CO2eq")
```

## What Gets Logged

When you run the example above, CodeCarbon creates an `emissions.csv` file in your working directory with columns including:

- `timestamp`: when the measurement was taken
- `duration`: how long the generation took
- `emissions`: CO2 in kg
- `energy_kwh`: energy consumed in kilowatt-hours
- `cpu_power`: CPU power in watts
- `gpu_power`: GPU power in watts (typically the dominant factor)

## Optimizing for Lower Emissions

You can reduce the carbon cost of image generation by adjusting inference parameters:

```python
# mktestdocs: skip
with EmissionsTracker() as tracker:
    # Fewer inference steps = faster generation, lower emissions
    # Trade-off: slightly lower image quality
    image = pipeline(prompt, num_inference_steps=20).images[0]

print(f"Optimized generation emissions: {tracker.final_emissions:.6f} kg CO2eq")
```

## Comparing Generation Approaches

To understand the trade-offs between different model sizes, inference steps, and their carbon impact, see [Comparing Model Efficiency](../tutorials/comparing-model-efficiency.md). You can apply the same patterns to compare different diffusion models or generation parameters.

## Next Steps

- [Configure CodeCarbon](configuration.md) to customize tracking behavior
- [Send emissions data to the cloud](cloud-api.md) to visualize emissions across multiple generation runs
- Explore other frameworks in [HuggingFace Transformers](transformers.md) or [local model agents](agents.md)
