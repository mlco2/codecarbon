# Track & reduce CO₂ emissions from your local computing

AI can benefit society in many ways, but given the energy needed to support the computing behind AI, these benefits can come at a high environmental price. Use CodeCarbon to track and reduce your CO₂ output from code running on your own hardware. For tracking emissions from remote GenAI API calls (OpenAI, Anthropic, etc.), see [EcoLogits](https://ecologits.ai/latest/?utm_source=codecarbon&utm_medium=docs).

## What we are

- **A lightweight, easy to use Python library** – Simple API to track emissions
- **Open source, free & community driven** – Built by and for the community
- **Effective visual outputs** – Put emissions in context with real-world equivalents

## Quickstart

### Python

Install CodeCarbon:

``` bash
pip install codecarbon
```

Track your code with a context manager:

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker()
tracker.start()

# Your code here

emissions = tracker.stop()
print(f"Emissions: {emissions} kg CO₂")
```

[**Learn more** →](tutorials/first-tracking.md)

### CLI

Track any command without changing your code:

``` bash
codecarbon monitor --no-api -- python train.py
```

Or detect your hardware:

``` bash
codecarbon detect
```

[**Learn more** →](tutorials/cli.md)

---

## Computer emits CO₂. We started measuring how much

A single datacenter can consume large amounts of energy to run computing code. An innovative new tracking tool is designed to measure the climate impact of artificial intelligence.

*Kana Lottick, Silvia Susai, Sorelle Friedler, and Jonathan Wilson.* [Energy Usage Reports: Environmental awareness as part of algorithmic accountability](http://arxiv.org/abs/1911.08354). *NeurIPS Workshop on Tackling Climate Change with Machine Learning, 2019.*

<div class="video-wrapper" markdown="1">>
<video width="640" height="360" controls >
    <source src="https://player.vimeo.com/external/482564729.hd.mp4?s=70d4f409870b0af74fa5e61d0d17bfe34a4d4282&profile_id=175" type="video/mp4">
  </video>
</div>

## Quick links

| Section | Description |
|---------|-------------|
| [Quickstart](tutorials/first-tracking.md) | Get started in 5 minutes |
| [Installation](how-to/installation.md) | Install CodeCarbon |
| [CLI Tutorial](tutorials/cli.md) | Track emissions from the command line |
| [Python API Tutorial](tutorials/python-api.md) | Track emissions in Python code |
| [Comparing Model Efficiency](tutorials/comparing-model-efficiency.md) | Measure carbon efficiency across ML models |
| [API Reference](reference/api.md) | Full parameter documentation |
| [Framework Examples](how-to/scikit-learn.md) | Example usage patterns |
| [Methodology](explanation/methodology.md) | How emissions are calculated |
| [EcoLogits](https://ecologits.ai/latest/?utm_source=codecarbon&utm_medium=docs) | Track emissions from GenAI API calls |
