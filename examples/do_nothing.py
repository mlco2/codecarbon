import logging
import time

from codecarbon import track_emissions


@track_emissions(
    project_name="just_sleep",
    emissions_endpoint="http://app-d6bc59c3-0f69-4d8b-a6a3-bc39a9ceb0c2.cleverapps.io",
    experiment_id="82ba0923-0713-4da1-9e57-cea70b460ee9",
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
