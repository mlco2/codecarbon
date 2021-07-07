import time

from codecarbon import track_emissions


@track_emissions(
    # api_endpoint="http://your api if you want",
    # experiment_id="3a202149-8be2-408c-a3d8-baeae2de2987",
    # api_key="not used yet",
    save_to_api=True,
)
def train_model():
    """
    This function will do nothing during (occurrence * delay) seconds.
    The Code Carbon API will be called every (measure_power_secs * api_call_interval)
    seconds.
    """
    occurrence = 60 * 24
    delay = 60  # Seconds
    for i in range(occurrence):
        print(f"{occurrence * delay - i * delay} seconds before ending script...")
        time.sleep(delay)


if __name__ == "__main__":
    train_model()
