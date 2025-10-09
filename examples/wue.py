import time

from codecarbon import track_emissions


@track_emissions(
    measure_power_secs=3,
    wue=1.1,
)
def train_model():
    """
    This function will do nothing.
    """
    print("30 seconds before ending script...")
    time.sleep(30)


if __name__ == "__main__":
    model = train_model()
