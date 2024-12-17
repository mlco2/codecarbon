import time

from codecarbon import track_emissions


@track_emissions(
    # api_endpoint="http://your api if you want",
    # experiment_id="584008e4-a081-4659-a97e-5629586ca69a",
    api_key="cpt_6gSSbpJ-bYUk6qSHgr1sAp_n076wTWzR0yGiDKzKAdY",
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
