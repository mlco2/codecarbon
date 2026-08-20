![banner](docs/images/banner.png)

# Track & reduce CO₂ emissions from your local computing

Estimate and track carbon emissions from your computer, quantify and analyze their impact.

[![](https://img.shields.io/pypi/v/codecarbon?color=024758)](https://pypi.org/project/codecarbon/) [![DOI](https://zenodo.org/badge/263364731.svg)](https://zenodo.org/badge/latestdoi/263364731) [![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/mlco2/codecarbon/badge)](https://scorecard.dev/viewer/?uri=github.com/mlco2/codecarbon) [![codecov](https://codecov.io/gh/mlco2/codecarbon/graph/badge.svg)](https://codecov.io/gh/mlco2/codecarbon) [![Discord](https://img.shields.io/badge/Discord-Join%20Community-7289da?logo=discord&logoColor=white)](https://discord.gg/GS9js2XkJR)

- **A lightweight, easy to use Python library** – Simple API to track emissions
- **Open source, free & community driven** – Built by and for the community
- **Effective visual outputs** – Put emissions in context with real-world equivalents

> **Tracking GenAI API calls?** CodeCarbon measures emissions from **local computing** (your hardware). To track emissions from remote GenAI API calls (OpenAI, Anthropic, Mistral, etc.), use [**EcoLogits**](https://ecologits.ai/). Both tools are complementary.

> **Join the community!** Have questions, want to share your work, or contribute? Join us on [**Discord**](https://discord.gg/GS9js2XkJR) – we're here to help and excited to hear from you!

## Installation

```bash
pip install codecarbon
```

If you use Conda:

```bash
conda activate your_env
pip install codecarbon
```

More installation options: [installation docs](https://docs.codecarbon.io/latest/how-to/installation/).

Something not working, or numbers that look wrong? See the
[troubleshooting guide](https://docs.codecarbon.io/latest/how-to/troubleshooting/).

## Quickstart (Python)

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker()
tracker.start()

# Your code here

emissions = tracker.stop()
print(f"Emissions: {emissions} kg CO₂")
```

[**Learn more** →](https://docs.codecarbon.io/latest/tutorials/first-tracking/)

## Quickstart (CLI)

Track a command without changing your code:

```bash
codecarbon monitor --no-api -- python train.py
```

Detect your hardware:

```bash
codecarbon detect
```

Full CLI guide: [CLI tutorial](https://docs.codecarbon.io/latest/tutorials/cli/).

## Configuration

You can configure CodeCarbon using:

- `~/.codecarbon.config` (global)
- `./.codecarbon.config` (project-local)
- `CODECARBON_*` environment variables
- Python arguments (`EmissionsTracker(...)`)

Configuration precedence and examples: [configuration guide](https://docs.codecarbon.io/latest/how-to/configuration/).

## How it works

We created a Python package that estimates your hardware electricity power consumption (GPU + CPU + RAM) and we apply to it the carbon intensity of the region where the computing is done.

CodeCarbon focuses on the main compute components it can measure or estimate directly: CPU, GPU, and RAM. It does not separately model disk I/O, network transfers, displays, cooling, or other peripherals because those sources are usually much smaller for local code-level experiments and are not exposed through the same low-overhead measurement interfaces.

On Linux, CodeCarbon reads Intel RAPL hardware energy counters when it can. If those counters are not readable it falls back to estimating from CPU load, which is less accurate — see [getting accurate CPU measurements](https://docs.codecarbon.io/latest/how-to/enable-rapl/) to enable them.

![calculation Summary](docs/images/calculation.png)

We explain more about this calculation in the [**Methodology**](https://docs.codecarbon.io/latest/explanation/methodology/) section of the documentation, and we document how close those numbers are — and where they are not close — in [**Accuracy and validation**](https://docs.codecarbon.io/latest/explanation/accuracy/).

## Visualize

You can visualize your experiment emissions on the [dashboard](https://dashboard.codecarbon.io/) or locally with [carbonboard](https://docs.codecarbon.io/latest/how-to/visualize/).

![dashboard](docs/images/dashboard.png)

## Quick links

| Section                                                                                               | Description                                |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| [Quickstart](https://docs.codecarbon.io/latest/tutorials/first-tracking/)                             | Get started in 5 minutes                   |
| [Installation](https://docs.codecarbon.io/latest/how-to/installation/)                                | Install CodeCarbon                         |
| [CLI Tutorial](https://docs.codecarbon.io/latest/tutorials/cli/)                                      | Track emissions from the command line      |
| [Python API Tutorial](https://docs.codecarbon.io/latest/tutorials/python-api/)                        | Track emissions in Python code             |
| [Comparing Model Efficiency](https://docs.codecarbon.io/latest/tutorials/comparing-model-efficiency/) | Measure carbon efficiency across ML models |
| [Accurate CPU measurements (Linux/RAPL)](https://docs.codecarbon.io/latest/how-to/enable-rapl/)       | Read real energy counters instead of estimating |
| [API Reference](https://docs.codecarbon.io/latest/reference/api/)                                     | Full parameter documentation               |
| [Framework examples (scikit-learn)](https://docs.codecarbon.io/latest/how-to/scikit-learn/)           | Task-oriented ML framework examples        |
| [Methodology](https://docs.codecarbon.io/latest/explanation/methodology/)                             | How emissions are calculated               |
| [Accuracy and validation](https://docs.codecarbon.io/latest/explanation/accuracy/)                    | How accurate the numbers are, and why      |
| [Alternatives comparison](https://docs.codecarbon.io/latest/explanation/alternatives/)                 | CodeCarbon vs other carbon tracking tools  |
| [When to use CodeCarbon vs EcoLogits](https://docs.codecarbon.io/latest/explanation/when-to-use/)     | Choose the right tool                      |
| [EcoLogits](https://ecologits.ai/)                                                                    | Track emissions from GenAI API calls       |
| [Discord Community](https://discord.gg/GS9js2XkJR)                                                    | Chat with us and the community             |

## Links

- [Main website](https://codecarbon.io) to learn why we do this.
- [Dashboard](https://dashboard.codecarbon.io/) to see your emissions.
- [Documentation](https://docs.codecarbon.io/) to learn how to use the package and our methodology.
- [EcoLogits](https://ecologits.ai/) to track emissions from GenAI API calls (OpenAI, Anthropic, etc.).
- [mlco2 on GitHub](https://github.com/mlco2) for our other open-source projects.
- [GitHub](https://github.com/mlco2/codecarbon) to look at the source code and contribute.
- [Discord](https://discord.gg/GS9js2XkJR) to chat with us.

## Contributing

We are hoping that the open-source community will help us edit the code and make it better!

You are welcome to open issues, even suggest solutions and better still contribute the fix/improvement! We can guide you if you're not sure where to start but want to help us out.

Check out our [contribution guidelines](https://github.com/mlco2/codecarbon/blob/master/CONTRIBUTING.md).

Feel free to chat with us on [Discord](https://discord.gg/GS9js2XkJR).

## Citation

If you find CodeCarbon useful for your research, use the **Cite this repository** button in the GitHub sidebar, or copy the BibTeX below. The DOI is a Zenodo concept DOI: it always resolves to the latest release. All versions and formats are on [Zenodo](https://doi.org/10.5281/zenodo.4658424).

```tex
@software{codecarbon,
  author       = {Benoit Courty and
                  Victor Schmidt and
                  Sasha Luccioni and
                  Boris Feld and
                  Jérémy Lecourt and
                  Mathilde Léval and
                  Luis Blanche and
                  Alexis Cruveiller and
                  Aditya Joshi and
                  Alexis Bogroff and
                  Hugues de Lavoreille and
                  Niko Laskaris and
                  Edoardo Abati and
                  Douglas Blank and
                  Ziyao Wang and
                  Armin Catovic and
                  Marc Alencon and
                  Michał Stęchły and
                  Christian Bauer and
                  Lucas Otávio N. de Araújo and
                  {The CodeCarbon contributors}},
  title        = {CodeCarbon: Estimate and track carbon emissions from computing},
  publisher    = {Zenodo},
  version      = {3.3.0},
  doi          = {10.5281/zenodo.4658424},
  url          = {https://doi.org/10.5281/zenodo.4658424}
}
```

## Contact

Feel free to chat with us on [Discord](https://discord.gg/GS9js2XkJR).

Codecarbon was formerly developed by volunteers from [**Mila**](http://mila.quebec) and the [**DataForGoodFR**](https://twitter.com/dataforgood_fr) community alongside donated professional time of engineers at [**Comet.ml**](https://comet.ml) and [**BCG GAMMA**](https://www.bcg.com/en-nl/beyond-consulting/bcg-gamma/default).

Now CodeCarbon is supported by [**Code Carbon**](https://www.helloasso.com/associations/code-carbon), a French non-profit organization whose mission is to accelerate the development and adoption of CodeCarbon.

## Sponsors

<div align="center">
  <a href="https://www.clever-cloud.com/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/mlco2/codecarbon-landing-page/main/public/assets/partners/clever_cloud.png">
      <img src="https://cdn.clever-cloud.com/uploads/2023/03/logoonwhite.svg" alt="Clever Cloud" height="48">
    </picture>
  </a>
  &nbsp;&nbsp;&nbsp;
  <a href="https://dataforgood.fr/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/mlco2/codecarbon-landing-page/main/public/assets/partners/dataforgood.png">
      <img src="https://dataforgood.fr/images/dataforgood.svg" alt="Data For Good" height="48">
    </picture>
  </a>
  &nbsp;&nbsp;&nbsp;
  <a href="https://github.com/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/mlco2/codecarbon-landing-page/main/public/assets/partners/GitHub.png">
      <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Logo.png" alt="GitHub" height="48">
    </picture>
  </a>
  &nbsp;&nbsp;&nbsp;
  <a href="https://www.mozilla.org/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/mlco2/codecarbon-landing-page/main/public/assets/partners/mozilla.svg">
      <img src="https://upload.wikimedia.org/wikipedia/commons/d/df/Mozilla_2024_logo.svg" alt="Mozilla" height="48">
    </picture>
  </a>
</div>
