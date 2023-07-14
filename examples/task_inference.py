from time import sleep

from codecarbon import EmissionsTracker


def load_dataset(dataset, split):
    print(f"Loading dataset {dataset} {split}")
    sleep(5)
    return dataset


def build_model():
    model = "huge_model"
    sleep(5)
    return model


def inference(model, data, inference_task_name):
    print(f"Running inference {inference_task_name} on {model} {data}")
    sleep(5)
    return "inference_result"


def main():
    tracker = EmissionsTracker(project_name="bert_inference", measure_power_secs=10)
    tracker.start()

    tracker.start_task("load dataset")
    dataset = load_dataset("imdb", split="test")
    tracker.stop_task()
    tracker.start_task("build model")
    model = build_model()
    tracker.stop_task()
    for i in range(2):
        inference_task_name = "Inference" + str(i)
        tracker.start_task(inference_task_name)
        inference(model, dataset, inference_task_name)
        tracker.stop_task()
    emissions = tracker.stop()

    print(f"Emissions : {1000 * emissions} g CO₂")
    for task_name, task in tracker._tasks.items():
        print(
            f"Emissions : {1000 * task.emissions_data.emissions} g CO₂ for task {task_name}"
        )
        print(
            f"\tEnergy : {1000 * task.emissions_data.cpu_energy} Wh {1000 * task.emissions_data.gpu_energy} Wh RAM{1000 * task.emissions_data.ram_energy}Wh"
        )
        print(
            f"\tPower CPU:{ task.emissions_data.cpu_power:.0f}W GPU:{ task.emissions_data.gpu_power:.0f}W RAM{ task.emissions_data.ram_power:.0f}W"
            + f" during {task.emissions_data.duration} seconds."
        )


if __name__ == "__main__":
    main()
