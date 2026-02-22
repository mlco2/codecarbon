# Frequently Asked Questions

## When should I use CodeCarbon vs EcoLogits?

Use **CodeCarbon** when you run code on hardware you control—training models, local inference, or any code on your machine, server, or cloud VM. Use **EcoLogits** when you call GenAI APIs (OpenAI, Anthropic, Mistral, etc.) and want to estimate the environmental impact of those requests. Both are complementary: CodeCarbon for local computing, EcoLogits for remote API inference.

## How accurate are your estimations?

It is hard to quantify the entirety of computing emissions, because there are many factors in play, notably the life-cycle emissions of computing infrastructure. We therefore only focus on the direct emissions produced by running the actual code, but recognize that there is much work to be done to improve this estimation.

## What are the sources of your energy carbon intensity data?

### For cloud computing:

- **Google Cloud**: Google publishes carbon intensity of electricity for [Google Cloud](https://cloud.google.com/sustainability/region-carbon).
- **AWS**: Amazon has not made datacenter carbon footprints publicly available.
- **Azure**: Microsoft has a Sustainability Calculator but does not publish datacenter carbon intensity.

### For private infrastructure:

- **Our World in Data**: When available, we use data from [ourworldindata.org](https://ourworldindata.org/grapher/carbon-intensity-electricity)
- **Global Petrol Prices**: We use the electricity mix from [globalpetrolprices.com](https://www.globalpetrolprices.com/energy_mix.php) multiplied by carbon intensity
- **Default**: When no data is available, we default to 475 gCO2.eq/kWh from [IEA](https://www.iea.org/reports/global-energy-co2-status-report-2019/emissions)

## How do I offset my emissions?

CodeCarbon provides emissions data that you can use with various carbon offset programs. Check our [examples](../getting-started/examples.md) for integration patterns.

## Does CodeCarbon work on Windows/Mac/Linux?

Yes! CodeCarbon supports:
- Linux (primary)
- macOS (Intel and Apple Silicon)
- Windows (experimental)

## Can I use CodeCarbon in a Docker container?

Yes. See our [Advanced Installation](../getting-started/advanced_installation.md) guide for Docker setup.

## How do I contribute to CodeCarbon?

We welcome contributions! Please see our [GitHub repository](https://github.com/mlco2/codecarbon) for contribution guidelines.

## Is my data sent anywhere?

By default, CodeCarbon saves emissions data locally. You can configure HTTP output to send data to your own endpoints. No data is sent to third parties without explicit configuration.

## What hardware does CodeCarbon support?

- **CPU**: x86, ARM (including Apple Silicon)
- **GPU**: NVIDIA GPUs via nvidia-smi
- **Cloud**: AWS, GCP, Azure metadata detection

## How do I report a bug?

Please open an issue on [GitHub](https://github.com/mlco2/codecarbon/issues) with:
- Your environment details
- Steps to reproduce
- Expected vs actual behavior
