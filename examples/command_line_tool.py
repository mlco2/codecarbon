"""
This example demonstrates how to use CodeCarbon with command line tools.

Here we measure the emissions of an speech-to-text with WhisperX.

"""

import subprocess

from codecarbon import EmissionsTracker

COMMAND = [
    ".venv/bin/whisperx",
    "/path/to/your_video.mp4",
    "--model",
    "large-v2",
    "--align_model",
    "WAV2VEC2_ASR_LARGE_LV60K_960H",
    "--batch_size",
    "4",
    "--compute_type",
    "int8",
]


def run_command_line_tool(command):
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")


if __name__ == "__main__":
    tracker = EmissionsTracker()
    tracker.start()
    try:
        run_command_line_tool(COMMAND)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        tracker.stop()

    emissions: float = tracker.stop()
    print(f"Emissions: {emissions * 1000:.2f} g.co2.eq")
