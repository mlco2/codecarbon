# Track & reduce CO₂ emissions from your local computing

AI can benefit society in many ways, but given the energy needed to support the computing behind AI, these benefits can come at a high environmental price. Use CodeCarbon to track and reduce your CO₂ output from code running on your own hardware. For tracking emissions from remote GenAI API calls (OpenAI, Anthropic, etc.), see [EcoLogits](https://ecologits.ai/latest/?utm_source=codecarbon&utm_medium=docs).

[**Get Started** →](getting-started/installation.md)

---

## What we are

- **A lightweight, easy to use Python library** – Simple API to track emissions
- **Open source, free & community driven** – Built by and for the community
- **Effective visual outputs** – Put emissions in context with real-world equivalents

## Computer emits CO₂. We started measuring how much

A single datacenter can consume large amounts of energy to run computing code. An innovative new tracking tool is designed to measure the climate impact of artificial intelligence.

*Kana Lottick, Silvia Susai, Sorelle Friedler, and Jonathan Wilson.* [Energy Usage Reports: Environmental awareness as part of algorithmic accountability](http://arxiv.org/abs/1911.08354). *NeurIPS Workshop on Tackling Climate Change with Machine Learning, 2019.*

<div class="video-wrapper" markdown="1">>
<video width="640" height="360" controls >
    <source src="https://player.vimeo.com/external/482564729.hd.mp4?s=70d4f409870b0af74fa5e61d0d17bfe34a4d4282&profile_id=175" type="video/mp4">
  </video>
</div>

## How it works

1. **Download package** – `pip install codecarbon`
2. **Embed the code** – Add a few lines to your script
3. **Run and track** – Emissions are measured automatically
4. **Visualize results** – See your impact in context

## Seamless integration

Only a few lines of code:

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker()
tracker.start()

# Your code here

emissions = tracker.stop()
print(f"Emissions: {emissions} kg CO₂")
```

## Quick links

| Section | Description |
|---------|-------------|
| [When to use CodeCarbon](introduction/when-to-use.md) | Local vs remote: CodeCarbon vs EcoLogits |
| [Installation](getting-started/installation.md) | Get started with CodeCarbon |
| [Usage](getting-started/usage.md) | Learn how to use CodeCarbon |
| [API Reference](getting-started/api.md) | Full API documentation |
| [Examples](getting-started/examples.md) | Example usage patterns |
| [Methodology](introduction/methodology.md) | How emissions are calculated |
