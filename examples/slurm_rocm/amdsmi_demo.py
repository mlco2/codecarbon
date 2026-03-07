#!/usr/bin/env python3

import amdsmi


def main():
    try:
        # Initialize AMD SMI
        amdsmi.amdsmi_init()

        # Get all GPU handles
        devices = amdsmi.amdsmi_get_processor_handles()

        if not devices:
            print("No AMD GPUs detected.")
            return

        for idx, device in enumerate(devices):
            print(f"\n===== GPU {idx} =====")

            # Get GPU metrics
            metrics = amdsmi.amdsmi_get_gpu_metrics_info(device)

            # Energy (microjoules)
            energy = metrics.get("energy_accumulator", None)

            # Power (microwatts)
            avg_power = metrics.get("average_socket_power", None)
            cur_power = metrics.get("current_socket_power", None)

            print(f"Energy accumulator      : {energy} uJ")
            print(f"Average socket power    : {avg_power} W")
            print(f"Current socket power    : {cur_power} W")

        amdsmi.amdsmi_shut_down()

    except Exception as e:
        print("Error:", str(e))


if __name__ == "__main__":
    main()
