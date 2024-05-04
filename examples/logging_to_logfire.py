import json
import time

from logfire import Logfire

from codecarbon import EmissionsTracker
from codecarbon.output import LoggerOutput


def train_model(epochs: int):
    """
    This function will do nothing during (occurrence * delay) seconds.
    """
    occurrence = epochs  # 60 * 24
    delay = 30  # Seconds
    for i in range(occurrence):
        print(f"{occurrence * delay - i * delay} seconds before ending script...")
        time.sleep(delay)


# FIXME: This is only to show how codecarbon can be compatible with logfire
# If we finally decide to use logfire, we will need to implement the logfire output method
class LogfireWrapper(Logfire):
    def __init__(self):
        super().__init__()
        self._log = super().log

    def log(self, severity, msg):
        data = json.loads(msg)
        print(data)
        # For each key of the dictionary, we will add the key to the message template
        msg_template = "Codecarbon output: "
        for key in data.keys():
            msg_template += "{" + key + "},"

        self._log(severity, msg_template, data)


if __name__ == "__main__":
    logger = LogfireWrapper()
    loggerOutput = LoggerOutput(logger=logger)
    tracker = EmissionsTracker(save_to_logger=True, logging_logger=loggerOutput)
    tracker.start()
    train_model(epochs=1)  # Each epoch last 30 secondes
    emissions: float = tracker.stop()
    print(f"Emissions: {emissions} kg")
