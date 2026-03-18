"""
Use CodeCarbon but without loading the AMD GPU.
pip install codecarbon
"""

import time

from codecarbon import track_emissions


@track_emissions(
    measure_power_secs=5,
    log_level="debug",
)
def train_model():
    """
    This function will do nothing.
    """
    print("10 seconds before ending script...")
    time.sleep(10)


if __name__ == "__main__":
    model = train_model()
