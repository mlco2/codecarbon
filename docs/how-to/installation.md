# Installing CodeCarbon {#installation}

!!! note "Python Support"

    We recommend using a [supported Python version](https://devguide.python.org/versions/).

## From PyPi repository

The package is hosted on the pip repository
[here](https://pypi.org/project/codecarbon/).

To install the package, run the following command in your terminal.

``` bash
pip install codecarbon
```

## Using Conda environments

If you're using Conda for environment management, you can install
CodeCarbon with pip in your Conda environment:

``` bash
conda create --name codecarbon
conda activate codecarbon
pip install codecarbon
```

!!! note "Conda Support"

    Starting from 3.3.0 we start to maintain again an official Conda packages on [conda-forge](https://anaconda.org/channels/conda-forge/packages/codecarbon/overview):


    ``` bash
    conda install -c conda-forge codecarbon
    ```

    The [channel `codecarbon`](https://anaconda.org/channels/codecarbon/packages/codecarbon/overview) is outdated.



## Dependencies

The following packages are used by the CodeCarbon package, and will be
installed along with the package itself:

``` bash
arrow
click
pandas
prometheus_client
psutil
py-cpuinfo
nvidia-ml-py
rapidfuzz
requests
questionary
rich
typer
```

Please refer to
[pyproject.toml](https://github.com/mlco2/codecarbon/blob/master/pyproject.toml)
for the latest list of the packages used.

## (Non-Python users) Standalone installer

If you are not using Python but would like to run CodeCarbon (for instance to use the [CodeCarbon Command line](../tutorials/cli.md)), we
provide a standalone installer.

Use curl to download and run the script:

``` bash
curl -LsSf https://codecarbon.io/scripts/install.sh | sh
```

For Windows (PowerShell):

``` powershell
powershell -ExecutionPolicy ByPass -c "irm https://codecarbon.io/scripts/install.ps1 | iex"
```
