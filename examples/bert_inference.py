from transformers import pipeline
from datasets import load_dataset
from codecarbon import EmissionsTracker


def build_model():
    model = pipeline('fill-mask', model='bert-base-uncased')
    return model


def main():
    tracker = EmissionsTracker(project_name="bert_inference", measure_power_secs=1)
    tracker.start()
    tracker.start_task("load dataset")
    dataset = load_dataset("imdb", split='test')
    tracker.stop_task("load dataset")
    tracker.start_task("build model")
    model = build_model()
    tracker.stop_task("build model")
    counter = 0
    for d in dataset['text']:
        inference_task_name = "Inference_" + str(counter)
        tracker.start_task(inference_task_name)
        model(d+ ' [MASK]')
        tracker.stop_task(inference_task_name)
        counter+=1
    emissions = tracker.stop()

    print(f"Emissions : {emissions} kg CO₂")
    for task_name, task in tracker._tasks.items():
        print(
            f"Emissions : {task.emissions_data.emissions} kg CO₂ for task {task_name}"
        )


if __name__ == "__main__":
    main()
