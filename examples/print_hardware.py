from codecarbon.emissions_tracker import EmissionsTracker

if __name__ == "__main__":
    tracker = EmissionsTracker(measure_power_secs=0, save_to_file=False)

    print("Detected Hardware:")
    hardware_info = tracker.get_detected_hardware()

    print(f"- Available RAM: {hardware_info['ram_total_size']:.3f} GB")
    print(
        f"- CPU count: {hardware_info['cpu_count']} thread(s) in {hardware_info['cpu_physical_count']} physical CPU(s)"
    )
    print(f"- CPU model: {hardware_info['cpu_model']}")
    print(f"- GPU count: {hardware_info['gpu_count']}")

    gpu_model_str = hardware_info["gpu_model"]
    if hardware_info.get("gpu_ids"):
        gpu_model_str += (
            f" BUT only tracking these GPU ids : {hardware_info['gpu_ids']}"
        )
    print(f"- GPU model: {gpu_model_str}")
