# Frequently Asked Questions

## When should I use CodeCarbon vs EcoLogits?

Use **CodeCarbon** when you run code on hardware you control—training models, local inference, or any code on your machine, server, or cloud VM. Use **EcoLogits** when you call GenAI APIs (OpenAI, Anthropic, Mistral, etc.) and want to estimate the environmental impact of those requests. Both are complementary: CodeCarbon for local computing, EcoLogits for remote API inference.

## How accurate are your estimations?

It depends on which measurement backend your machine offers. With hardware energy counters (RAPL on Linux, NVML or amdsmi for GPUs) CodeCarbon reads real energy consumption. Without them it falls back to estimating CPU power from load and TDP, which on the machines we profiled deviated from RAPL by up to roughly a factor of two in either direction. Carbon intensity is a separate and often larger error source: without regional data CodeCarbon uses a world average of 475 gCO2.eq/kWh.

We also only cover the direct emissions of running the code — CPU, GPU and RAM — and not the life-cycle emissions of the hardware.

See [Accuracy and validation](accuracy.md) for the measured figures, the known gaps, and how to improve your own numbers.

## How does CodeCarbon compare to other carbon tracking tools?

See [CodeCarbon and the alternatives](alternatives.md), which covers carbontracker, eco2AI, experiment-impact-tracker, Zeus, Scaphandre, ML CO2 Impact and cloud provider tooling — including the cases where one of those is the better choice.

Accuracy also depends on your own machine. On Linux, CodeCarbon reads real CPU energy counters when they are readable, and otherwise estimates from CPU load and the processor's TDP, which is materially less accurate. See the next question.

## Why are my measurements estimates instead of real readings?

On Linux, CodeCarbon reads the Intel RAPL hardware energy counters under `/sys/class/powercap`. Since a kernel security fix these files are root-only by default, so CodeCarbon often cannot read them and falls back to estimating CPU power from CPU load and the processor's TDP. You will see a `RAPL - Permission denied` warning in the logs when this happens, but the warning is easy to miss in a notebook, a training framework that reconfigures logging, or a CI job.

The fix takes about two minutes and persists across reboots: see [Improve Measurement Accuracy with RAPL](../how-to/enable-rapl.md). The one-line `sudo chmod -R a+r /sys/class/powercap/*` also works but is reset on the next restart.

Note that RAPL counters do not exist at all in most containers and virtual machines, so estimation is expected there.

## What are the sources of your energy carbon intensity data?

### For cloud computing:

- **Google Cloud**: Google publishes carbon intensity of electricity for [Google Cloud](https://cloud.google.com/sustainability/region-carbon).
- **AWS**: Amazon has not made datacenter carbon footprints publicly available.
- **Azure**: Microsoft has a Sustainability Calculator but does not publish datacenter carbon intensity.

### For private infrastructure:

- **Our World in Data**: When available, we use data from [ourworldindata.org](https://ourworldindata.org/grapher/carbon-intensity-electricity)
- **Global Petrol Prices**: We use the electricity mix from [globalpetrolprices.com](https://www.globalpetrolprices.com/energy_mix.php) multiplied by the [carbon intensity of the source of electricity](https://github.com/mlco2/codecarbon/blob/master/codecarbon/data/private_infra/carbon_intensity_per_source.json)
- **Default**: When no data is available, we default to 475 gCO2.eq/kWh from [IEA](https://www.iea.org/reports/global-energy-co2-status-report-2019/emissions)

## How do I offset my emissions?

There are many offsetting schemes, and it is hard to recommend any single one. For one-shot offsetting, the [Gold Standard](https://www.goldstandard.org/) is often used, and has many offsetting projects to choose from at different prices. There are often local initiatives as well, so try researching what exists in your region/country. For a recurring offset, [Project Wren](https://projectwren.com/) lets you estimate your monthly carbon emissions and offset them via a monthly subscription. Keep in mind that offsetting is a good choice, but **reducing your emissions** should be the priority.

## Does CodeCarbon work on Windows/Mac/Linux?

Yes! CodeCarbon supports:
- Linux (primary)
- macOS (Intel and Apple Silicon)
- Windows (experimental)

## Can I use CodeCarbon in a Docker container?

Yes. CodeCarbon can be installed and used in Docker containers just like any other Python package using `pip install codecarbon`. Refer to the [installation guide](../how-to/installation.md) for details.

## How can I help?

If you find any functionality missing in the CodeCarbon repo, please [open an issue](https://github.com/mlco2/codecarbon/issues) so that you (and others!) can help add it. We did our best to cover all use cases and options, but we count on the open source community to help make the package an even greater success. You can also discuss ideas on [Discord](https://discord.gg/GS9js2XkJR) before diving into development.

## Is my data sent anywhere?

By default, CodeCarbon saves emissions data locally. You can configure HTTP output to send data to your own endpoints. We do send data to our API when the user allows it and logs in. No data is sent to third parties without explicit configuration.

## Why is my second tracker faster than the first?

In a single Python process, the first tracker pays a one-time cost to detect hardware (CPU model, GPU devices, RAM, power backends, and related setup). Later trackers in the same process reuse that cached setup, so `start()` and `stop()` are much faster on warm runs. This is expected: each new process still performs a full cold setup once.

## What hardware does CodeCarbon support?

CodeCarbon supports various CPU architectures, GPUs, and cloud providers. For details on measurement priority and supported hardware, see the [Methodology](methodology.md#which-backend-gets-chosen) page.

## How do I report a bug?

First check the [Troubleshooting](../how-to/troubleshooting.md) guide — most
warnings CodeCarbon prints are explained there, along with the fix.

If it is still a bug, please open an issue on [GitHub](https://github.com/mlco2/codecarbon/issues) with:
- Your environment details
- Steps to reproduce
- Expected vs actual behavior

You can also report bugs and ask for help on [Discord](https://discord.gg/GS9js2XkJR) where we can provide quick guidance.
