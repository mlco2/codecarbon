from datasets import load_dataset
from transformers import pipeline

from codecarbon import EmissionsTracker

device = "cuda"


def build_model():
    model = pipeline("fill-mask", model="bert-base-uncased", device=0)
    return model


def main():
    tracker = EmissionsTracker(project_name="bert_inference", measure_power_secs=0.1)
    tracker.start()
    tracker.start_task("load dataset")
    dataset = load_dataset("imdb", split="test")
    tracker.stop_task()
    tracker.start_task("build model")
    model = build_model()
    tracker.stop_task()
    counter = 0
    for d in dataset[:100]["text"]:
        d = " ".join(d.split())[:50]
        inference_task_name = "Inference"
        tracker.start_task(inference_task_name)
        print(model(d + " [MASK]"))
        tracker.stop_task()
        counter += 1

    emissions = tracker.stop()

    print(f"Emissions : {1000 * emissions} g CO₂")
    for task_name, task in tracker._tasks.items():
        print(
            f"Emissions : {1000 * task.emissions_data.emissions} g CO₂ for task {task_name}"
        )


if __name__ == "__main__":
    main()
