import logging
import time

from codecarbon import track_emissions


@track_emissions(project_name="just_sleep", emissions_endpoint="http://localhost:8008")
def train_model():
    for i in range(20):
        print("Waiting 10 more seconds...")
        time.sleep(10)


if __name__ == "__main__":
    logger = logging.getLogger("codecarbon")
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)
    print(logger.level)
    logger.debug("DEBUG")
    logger.info("INFO")
    logger.error("ERROR")
    model = train_model()
