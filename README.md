![banner](docs/edit/images/banner.png)

Estimate and track carbon emissions from your compute, quantify and analyze their impact.

[**Documentation**](https://mlco2.github.io/codecarbon)

<br/>

[![](https://img.shields.io/conda/v/codecarbon/codecarbon?color=C9FB37)](https://anaconda.org/codecarbon/codecarbon)
[![](https://img.shields.io/pypi/v/codecarbon?color=024758)](https://pypi.org/project/codecarbon/)
[![DOI](https://zenodo.org/badge/263364731.svg)](https://zenodo.org/badge/latestdoi/263364731)


- [About CodeCarbon](#about-codecarbon)
- [Installation](#installation)
- [Infrastructure Support](#infrastructure)
- [Quickstart](#quickstart)
- [Examples](#examples)
- [Data Sources](#data-source)
- [Contributing](#contributing)
- [Built-in Visualization Tool](#built-in-visualization-tool)
- [Build Documentation](#build-documentation)
- [Comet Integration](#comet-integration)
- [Report your emissions: LateX template](#report-your-emissions-latex-template)


# About CodeCarbon

While computing currently represents roughly 0.5% of the world’s energy consumption, that percentage is projected to grow beyond 2% in the coming years, which will entail a significant rise in global CO2 emissions if not done properly. Given this increase, it is important to quantify and track the extent and origin of this energy usage, and to minimize the emissions incurred as much as possible.

For this purpose, we created **CodeCarbon**, a Python package for tracking the carbon emissions produced by various kinds of computer programs, from straightforward algorithms to deep neural networks.

By taking into account your computing infrastructure, location, usage and running time, CodeCarbon can provide an estimate of how much CO<sub>2</sub> you produced, and give you some comparisons with common modes of transporation to give you an order of magnitude.

Our hope is that this package will be used widely for estimating the carbon footprint of computing, and for establishing best practices with regards to the disclosure and reduction of this footprint.

Follow the steps below to set up the package and don't hesitate to open an issue if you need help!


# Installation
Create a virtual environment using `conda` for easier management of dependencies and packages.
For installing conda, follow the instructions on the [official conda website](https://docs.conda.io/projects/conda/en/latest/user-guide/install/)

```
conda create --name codecarbon python=3.6
conda activate codecarbon
```

### Install from PyPI repository

```
pip install codecarbon
```

### Install from Conda repository

```
conda install -c codecarbon -c conda-forge codecarbon
```

`codecarbon` is now installed in your the local environment


# Infrastructure Support
Currently the package supports following hardware infrastructure.

### GPU
- Tracks Nvidia GPUs power consumption using pynvml library, pynvml is installed with the package install.

### CPU

#### On Windows and Mac
- Tracks Intel Processors power consumption using Intel Power Gadget
- Please install Intel Power Gadget [here](https://software.intel.com/content/www/us/en/develop/articles/intel-power-gadget.html).

*Note:* Please ensure that the Intel Power Gadget has the [required security permissions](https://osxdaily.com/2019/03/03/install-intel-power-gadget-mac/) on MacOS.


#### On Linux
- Tracks Intel Processors power consumption from Intel RAPL files at `/sys/class/powercap/intel-rapl`, [reference](http://web.eece.maine.edu/~vweaver/projects/rapl/)

*Note:* The Power Consumption will be tracked only if the RAPL files exist at the above mentioned path.


#### Fall back mode
If none of those tools are available to track the power consumptions, CodeCarbon will be switched to a fall back mode: It will first detect which CPU hardware is currently in use, and then map it to a data source listing 2000+ Intel and AMD CPUs and their corresponding thermal design powers (TDPs). If the CPU is not found in the data source, a global constant (85 Watt) will be applied. CodeCarbon assumes that 50% of the TDP will be the average power consumption to make this approximation.



# Quickstart

### Online mode
This is the most straightforward usage of the package, which is possible if you have access to the Internet, which is necessary to gather information regarding your geographical location.

```python
from codecarbon import EmissionsTracker
tracker = EmissionsTracker()
tracker.start()
# GPU Intensive code goes here
tracker.stop()
```
You can also use the decorator:

```python
from codecarbon import track_emissions

@track_emissions
def training_loop():
   pass
```

### Offline mode

This mode can be used in setups without internet access, but requires a manual specification of your country code.
A complete list of country ISO codes can be found on [Wikipedia](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes).

The offline tracker can be used as follows:
```python
from codecarbon import OfflineEmissionsTracker

tracker = OfflineEmissionsTracker(country_iso_code="CAN")
tracker.start()
# GPU Intensive code goes here
tracker.stop()
```

or by using the decorator:

```python
from codecarbon import track_emissions

@track_emissions(offline=True, country_iso_code="CAN")
def training_loop():
   pass
```

### Using comet.ml

Nothing to do here 🚀 ! Comet automatically logs your emissions if you have CodeCarbon installed. More about comet and adding the CodeCarbon panel to your project in [Comet Integration](#comet-integration).



# Examples

As an illustration of how to use CodeCarbon, we created a simple example using TensorFlow for digit classification on the [MNIST dataset](http://yann.lecun.com/exdb/mnist/):

First, install Tensorflow  2.0:

```
pip install tensorflow
```

Then, run the examples in the [`examples/`](/examples/) folder, which will call the online version of the Emissions tracker by default:

```
python examples/mnist.py
python examples/mnist_decorator.py
```

This will create a `.csv` file with information about the energy that you used to carry out the classification task, and an estimate of the CO<sub>2</sub> that you generated, complete with comparisons to common modes of transportation to give you a better idea of the order of magnitude of your emissions.



# Data Source

To find the carbon efficiency of your cloud region, you can look into [CodeCarbon's cloud data](https://github.com/mlco2/codecarbon/tree/master/codecarbon/data/cloud).
If you are using a private infrastructure you can look into the [CodeCarbon's private infrastructure](https://github.com/mlco2/codecarbon/tree/master/codecarbon/data/private_infra/2016).
[A number of resources](https://github.com/mlco2/impact/tree/master/data#mlco2s-data) can help you find the carbon efficiency of you local grid if you cannot find it in the previous links.



# Contributing

We are hoping that the open-source community will help us edit our code and make it better!
If you want to contribute, make sure that the [`tox` package](https://tox.readthedocs.io/en/latest/example/package.html) is available to run tests and debug:

```
pip install tox
```

You can run tests by simply entering tox in the terminal when in the root package directory, and it will run the predefined tests.

```
tox
```
In order to contribute a change to our code base, please submit a pull request (PR) via GitHub and someone from our team will go over it and accept it.



# Built-in Visualization Tool
To track the evolution of your CO<sub>2</sub> emissions or just to see some nice graphs and charts, you can use the visualization tool that we created.
As input, it takes a .csv file in the format generated by the Emissions Tracker, and it generates a visualization of the emissions incurred.

You can run try it out on a sample data file such as the one in `examples/emissions.csv`, and run it with the following command from the code base:
```
python codecarbon/viz/carbonboard.py --filepath="examples/emissions.csv"
```

If you have the package installed, you can run the CLI command:

```
carbonboard --filepath="examples/emissions.csv" --port=xxxx
```


Once you have generated your own .csv file based on your computations, you can feed that into the visualization tool to see a more visual representation of your own emissions.

![Dashboard Summary](docs/edit/images/summary.png)

You can also see the carbon intensity of different regions and countries:

![Global Equivalents](docs/edit/images/global_equivalents.png)

As well as the relative carbon intensity of different compute regions of cloud providers:

![Cloud Emissions](docs/edit/images/cloud_emissions.png)



# Build Documentation
No software is complete without great documentation!
To make generating documentation easier, install the [`sphinx` package](https://www.sphinx-doc.org/en/master/usage/installation.html#installation-from-pypi) and use it to edit and improve the existing documentation:
```
pip install -U sphinx sphinx_rtd_theme
cd docs/edit
make docs
```
In order to make changes, edit the `.rst` files that are in the `/docs/edit` folder, and then run:
```
make docs
```
to regenerate the html files.


# Comet Integration

**CodeCarbon** automatically integrates with [Comet](https://www.comet.ml/site) for experiment tracking and visualization. Comet provides data scientists with powerful tools to track, compare, explain and reproduce their experiments, and now with **CodeCarbon** you can easily track the carbon footprint of your jobs along with your training metrics, hyperparameters, dataset samples, artifacts and more.

![](docs/edit/images/comet-workspace.png)

To get started with the **Comet**-**CodeCarbon** integration, make sure you have `comet-ml` installed:

```
pip install comet_ml>=3.2.2
```

The minimum Comet version

Go to [Comet's website](https://www.comet.ml/signup) and create a free account. From your account settings page, copy your personal API key.

In the [`mnist-comet.py`](examples/mnist-comet.py) example file, replace the placeholder code with your API key:

```
experiment = Experiment(api_key="YOUR API KEY")
```

Run your experiment and click on the link in stdout to be taken back to the Comet UI. Automatically you'll see your metrics, hyperparameters, graph definition, system and environment details and more.

**Comet** will automatically create an `EmissionsTracker` object from the `codecarbon` package when your code runs. To visualize the carbon footprint of your experiment, go to the `Panels` tab in the left sidebar and click `Add Panel`.

From the Panel Gallery click the `Public` tab and search for `CodeCarbon Footprint`. Once you've found it, add it to your Experiment.

![](docs/edit/images/panel-gallery.gif)

Now back in the `Panels` tab you'll see your CodeCarbon Footprint visualization in the Comet UI. To render the visualization by default, save your `View`. And voilà! Every time you run your experiments, you'll be able to visualize your CodeCarbon emissions data alongside everything else you need to track for your research.

![](docs/edit/images/codecarbon-panel.png)



# Report your emissions: LateX template

We believe that an important step towards reducing carbon emissions is the generalization of emissions reporting in papers, blog posts and publications in general. Here's an example LateX snippet you might want to use:

```latex
\usepackage{hyperref}

\subsection{CO2 Emission Related to Experiments}

Experiments were conducted using {cloud provider} in {region}, which has a carbon efficiency of {carbon efficiency} kgCO$_2$eq/kWh. A cumulative of {hours used} hours of computation was performed on hardware of type {hardware type} (TDP of W).

Total emissions are estimated to be {emission} kgCO$_2$eq of which {percentage offset} percents were directly offset by the cloud provider.

%Uncomment if you bought additional offsets:
%XX kg CO2eq were manually offset through \href{link}{Offset Provider}.

Estimations were conducted using the \href{https://github.com/mlco2/codecarbon}{CodeCarbon emissions tracker}, a joint effort from authors of \cite{lacoste2019quantifying} and \cite{lottick2019nergy}.

@article{lacoste2019quantifying,
  title={Quantifying the Carbon Emissions of Machine Learning},
  author={Lacoste, Alexandre and Luccioni, Alexandra and Schmidt, Victor and Dandres, Thomas},
  journal={Workshop on Tackling Climate Change with Machine Learning at NeurIPS 2019},
  year={2019}
}

@article{lottick2019nergy,
    title={Energy Usage Reports: Environmental awareness as part of algorithmic
  accountability},
    author={Kadan Lottick and Silvia Susai and Sorelle A. Friedler and Jonathan P. Wilson},
    year={2019},
    journal={Workshop on Tackling Climate Change with Machine Learning at NeurIPS 2019}
}
```

### Citing CodeCarbon

```
@article{codecarbon,
  author={Victor Schmidt and Kamal Goyal and Aditya Joshi and Boris Feld and Liam Conell and Nikolas Laskaris and Doug Blank and Jonathan Wilson and Sorelle Friedler and Sasha Luccioni},
  title={{CodeCarbon: Estimate and Track Carbon Emissions from Machine Learning Computing}},
  year={2021},
  howpublished={\url{https://github.com/mlco2/codecarbon}},
  DOI={10.5281/zenodo.4658424},
  publisher={Zenodo},
}
```
