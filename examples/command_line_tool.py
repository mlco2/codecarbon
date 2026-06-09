"""
This example demonstrates how to use CodeCarbon with command line tools.

⚠️  IMPORTANT LIMITATION:
CodeCarbon tracks emissions at the MACHINE level when monitoring external commands
via subprocess. It measures total system power during the command execution, which
includes the command itself AND all other system processes.

For accurate process-level tracking, the tracking code must be embedded in the
application being measured (not possible with external binaries like WhisperX).

This example measures emissions during WhisperX execution, but cannot isolate
WhisperX's exact contribution from other system activity.
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
