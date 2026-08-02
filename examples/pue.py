import time

from codecarbon import track_emissions


@track_emissions(
    measure_power_secs=3,
    pue=2,
    force_carbon_intensity_g_co2e_kwh=1,
    log_level="DEBUG",
)
def train_model():
    """
    This function will do nothing.
    """
    print("30 seconds before ending script...")
    time.sleep(30)


if __name__ == "__main__":
    model = train_model()
