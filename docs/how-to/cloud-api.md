# Use the Cloud API & Dashboard

!!! warning "API mode"

    This mode uses the CodeCarbon API to upload the timeseries of your
    emissions on a central server.

    Thanks to [CleverCloud](https://www.clever.cloud/) the use of API is
    free as soon as it remains under certain limits.

![CodeCarbon architecture](https://github.com/mlco2/codecarbon/raw/master/carbonserver/Images/code_carbon_archi.png){.align-center width="700px" height="400px"}

![CodeCarbon database](https://github.com/mlco2/codecarbon/raw/master/carbonserver/Images/CodecarbonDB.jpg){.align-center width="700px"}

## Prerequisites

1. Create an account on the [CodeCarbon dashboard](https://dashboard.codecarbon.io/)
2. Run `codecarbon login` from your terminal (see the [CLI tutorial](../tutorials/cli.md) for setup details)

This will create an experiment_id for the default project and save it to
`.codecarbon.config`.

## Send emissions from your code

``` python
from codecarbon import track_emissions

@track_emissions(save_to_api=True)
def train_model():
    # GPU intensive training code  goes here

if __name__ =="__main__":
    train_model()
```

More options could be specified in `@track_emissions` or in
`.codecarbon.config`

The [CodeCarbon dashboard](https://dashboard.codecarbon.io/) use
[CodeCarbon API](https://api.codecarbon.io/) to get the data

The API do not have a nice web interface to create your own organization
and project, you have to use [OpenAPI
interface](https://api.codecarbon.io/docs) for that.

And so on for your team, project and experiment.

You then have to set your experiment id in CodeCarbon, with two options:

In the code:

``` python
from codecarbon import track_emissions

@track_emissions(
    measure_power_secs=30,
    api_call_interval=4,
    experiment_id="your experiment id",
    save_to_api=True,
)
def train_model():
    ...
```

Or in the config file `.codecarbon.config`:

``` ini
[codecarbon]
experiment_id = your experiment id
save_to_api = true
```

Once your experiments are running, [visualize your emissions](visualize.md) on the dashboard or locally with carbonboard.
