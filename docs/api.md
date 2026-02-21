# CodeCarbon API {#api}

## CodeCarbon API

!!! note "Warning"

This mode use the CodeCarbon API to upload the timeseries of your
emissions on a central server.

Thanks to [CleverCloud](https://www.clever.cloud/) the use of API is
free as soon as it remains under certain limits.
!!! note
   ![Summary](https://github.com/mlco2/codecarbon/raw/master/carbonserver/Images/code_carbon_archi.png){.align-center
width="700px" height="400px"}

![Summary](https://github.com/mlco2/codecarbon/raw/master/carbonserver/Images/CodecarbonDB.jpg){.align-center
width="700px"}

Before using it, you need to create on account on the [CodeCarbon
dashboard](https://dashboard.codecarbon.io/)

Then login from your terminal:

``` console
codecarbon login
```

It will create an experiment_id for the default project and save it to
`codecarbon.config`

Then you can tell CodeCarbon to monitor your machine:

``` console
codecarbon monitor
```

Or use the API in your code:

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

You then have to set you experiment id in CodeCarbon, with two options:

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

Or in the config file \`.codecarbon.config\`:

``` ini
[codecarbon]
experiment_id = your experiment id
save_to_api = true
```
