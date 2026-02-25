# Installing CodeCarbon {#installation}

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

!!! note "Note"

    While CodeCarbon can be used in Conda environments, we no longer
    maintain Conda packages. We recommend using `pip install codecarbon`
    within your Conda environment, which works seamlessly with Conda.

!!! note "Note"

    We recommend using Python 3.8 or above.

## Dependencies

The following packages are used by the CodeCarbon package, and will be
installed along with the package itself:

``` bash
arrow
click
fief-client[cli]
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

If you are not using Python but would like to run CodeCarbon (for instance to use the [CodeCarbon Command line](usage.md#usage-command-line)), we
provide a standalone installer.

Use curl to download and run the script:

``` bash
curl -LsSf https://codecarbon.io/scripts/install.sh | sh
```

For Windows (PowerShell):

``` powershell
powershell -ExecutionPolicy ByPass -c "irm https://codecarbon.io/scripts/install.ps1 | iex"
```
