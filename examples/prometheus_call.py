import logging
import time

from codecarbon import track_emissions
from codecarbon.external.logger import logger


@track_emissions(
    measure_power_secs=5,
    api_call_interval=3,
    save_to_prometheus=True,
)
def train_model():
    """
    This function will do nothing during (occurrence * delay) seconds.
    The Code Carbon API will be called every (measure_power_secs * api_call_interval) seconds.
    """
    occurrence = 60 * 24 * 365 * 100  # Run for 100 years !
    delay = 60  # Seconds
    for i in range(occurrence):
        print(f"{occurrence * delay - i * delay} seconds before ending script...")
        time.sleep(delay)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler("codecarbon.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)-12s: %(levelname)-8s %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.debug("GO!")
    model = train_model()
    logger.debug("THE END!")
