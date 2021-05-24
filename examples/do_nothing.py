import logging
import time

from codecarbon import track_emissions


@track_emissions(
    project_name="just_sleep",
    emissions_endpoint="http://localhost:8008",
    measure_power_secs=15,
    measure_occurrence_before_calling_api=4,
)
def train_model():
    occurence = 20
    delay = 10
    for i in range(occurence):
        print(f"{occurence * delay - i * delay} seconds before ending script...")
        time.sleep(delay)


if __name__ == "__main__":
    logger = logging.getLogger("codecarbon")
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(logging.ERROR)
    print(logger.level)
    logger.debug("DEBUG messages will be printed.")
    logger.info("INFO messages will be printed.")
    logger.error("ERROR messages will be printed.")
    model = train_model()
