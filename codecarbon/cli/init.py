from codecarbon.core.api_client import ApiClient, get_datetime_with_timezone
from codecarbon.core.schemas import ExperimentCreate

DEFAULT_PROJECT_ID = "e60afa92-17b7-4720-91a0-1ae91e409ba1"


if __name__ == "__main__":
    api = ApiClient()
    experiment = ExperimentCreate(
        timestamp=get_datetime_with_timezone(),
        name="Code Carbon user test",
        description="Code Carbon user test with default project",
        on_cloud=False,
        project_id=DEFAULT_PROJECT_ID,
        country_name="France",
        country_iso_code="FRA",
        region="france",
    )
    experiment_id = api.add_experiment(experiment)
    print(f"Welcome to CodeCarbone, here is your experiment id : {experiment_id}")
