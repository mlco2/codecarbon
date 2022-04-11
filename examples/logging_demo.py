import argparse
import logging
import time

import google.cloud.logging

from codecarbon import EmissionsTracker
from codecarbon.output import GoogleCloudLoggerOutput, LoggerOutput


def train_model(epochs: int):
    """
    This function will do nothing during (occurrence * delay) seconds.
    The Code Carbon API will be called every (measure_power_secs * api_call_interval)
    seconds.
    """
    occurrence = epochs  # 60 * 24
    delay = 30  # Seconds
    for i in range(occurrence):
        print(f"{occurrence * delay - i * delay} seconds before ending script...")
        time.sleep(delay)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--google-project",
        help="Specify the name of the Google project (for Cloud Logging)",
    )
    args = parser.parse_args()

    log_name = "code_carbone"
    if args.google_project:
        client = google.cloud.logging.Client(project=args.google_project)
        external_logger = GoogleCloudLoggerOutput(client.logger(log_name))
    else:
        external_logger = logging.getLogger(log_name)
        channel = logging.FileHandler(log_name + ".log")
        external_logger.addHandler(channel)
        external_logger.setLevel(logging.INFO)
        external_logger = LoggerOutput(external_logger, logging.INFO)

    tracker = EmissionsTracker(save_to_logger=True, logging_logger=external_logger)
    tracker.start()
    train_model(epochs=1)  # Each epoch last 30 secondes
    emissions: float = tracker.stop()
    print(f"Emissions: {emissions} kg")
