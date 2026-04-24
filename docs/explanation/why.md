# Motivation

AI can benefit society in many ways, but given the energy needed to support the computing behind AI, these benefits can come at a high environmental price. Use CodeCarbon to track and reduce your CO₂ output from **local computing**—training, inference on your own hardware, or any code on machines you control. For tracking emissions from remote GenAI API calls, see [EcoLogits](https://ecologits.ai/latest/?utm_source=codecarbon&utm_medium=docs).

## Computer emits CO₂. We started measuring how much

A single datacenter can consume large amounts of energy to run computing code. An innovative new tracking tool is designed to measure the climate impact of artificial intelligence.

*Kana Lottick, Silvia Susai, Sorelle Friedler, and Jonathan Wilson.* [Energy Usage Reports: Environmental awareness as part of algorithmic accountability](http://arxiv.org/abs/1911.08354). *NeurIPS Workshop on Tackling Climate Change with Machine Learning, 2019.*

## Why track emissions?

In recent years, Artificial Intelligence, and more specifically Machine Learning, has become remarkably efficient at performing human-level tasks: recognizing objects and faces in images, driving cars, and playing sophisticated games like chess and Go.

In order to achieve these incredible levels of performance, current approaches leverage vast amounts of data to learn underlying patterns and features. Thus, state-of-the-art Machine Learning models leverage significant amounts of computing power, training on advanced processors for weeks or months, consequently consuming enormous amounts of energy. Depending on the energy grid used during this process, this can entail the emission of large amounts of greenhouse gases such as CO₂.

With AI models becoming more ubiquitous and deployed across different sectors and industries, AI's environmental impact is also growing. For this reason, it is important to estimate and curtail both the energy used and the emissions produced by training and deploying AI models. This package enables developers to track carbon dioxide (CO₂) emissions across machine learning experiments or other programs.

## How to get started

You can start tracking emissions in just a few lines of Python:

``` python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker()
tracker.start()

# Your code here
# e.g., model training, data processing, etc.

emissions = tracker.stop()
print(f"Emissions: {emissions} kg CO₂eq")
```

Or track any command from the CLI without modifying your code:

``` bash
codecarbon monitor -- python train.py
```

## CO₂-equivalents

This package enables developers to track emissions, measured as kilograms of CO₂-equivalents (CO₂eq) in order to estimate the carbon footprint of their work. We use *CO₂-equivalents [CO₂eq]*, which is a standardized measure used to express the global warming potential of various greenhouse gases: the amount of CO₂ that would have the equivalent global warming impact. For computing, which emits CO₂ via the electricity it consumes, carbon emissions are measured in kilograms of CO₂-equivalent per kilowatt-hour. Electricity is generated as part of the broader electrical grid by combusting fossil fuels, for example.
