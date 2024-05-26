import time

from codecarbon import track_emissions


@track_emissions(
    measure_power_secs=5,
    api_call_interval=1,
    save_to_logfire=True,
)
def train_model():
    """
    This function will do nothing during (occurrence * delay) seconds.
    The Logfire API will be called every (measure_power_secs * api_call_interval) seconds.
    """
    occurrence = 60  # seconds
    delay = 1  # Seconds
    for i in range(occurrence):
        print(f"{occurrence * delay - i * delay} seconds before ending script...")
        time.sleep(delay)


if __name__ == "__main__":
    train_model()
