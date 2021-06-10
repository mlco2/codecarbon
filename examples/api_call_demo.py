import time

from codecarbon import track_emissions


@track_emissions(
    project_name="just_sleep",
    api_endpoint="http://app-d6bc59c3-0f69-4d8b-a6a3-bc39a9ceb0c2.cleverapps.io",
    experiment_id="82ba0923-0713-4da1-9e57-cea70b460ee9",
    api_key="12aaaaaa-0b23-1234-1234-abcdef123456",
)
def train_model():
    """
    This function will do nothing during (occurence * delay) seconds.
    The Code Carbon API will be called every (measure_power_secs * api_call_interval) seconds.
    """
    occurence = 60 * 24
    delay = 60  # Seconds
    for i in range(occurence):
        print(f"{occurence * delay - i * delay} seconds before ending script...")
        time.sleep(delay)


if __name__ == "__main__":
    train_model()
