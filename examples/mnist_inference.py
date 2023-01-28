import tensorflow as tf
from sklearn.model_selection import GridSearchCV
from tensorflow.keras.wrappers.scikit_learn import KerasClassifier

from codecarbon import EmissionsTracker
from codecarbon.emissions_tracker import TaskEmissionsTracker, track_task_emissions

tracker = EmissionsTracker(
    project_name="mnist_inference", measure_power_secs=0.1, log_level="error"
)


def build_model():
    model = tf.keras.models.Sequential(
        [
            tf.keras.layers.Flatten(input_shape=(28, 28)),
            tf.keras.layers.Dense(128, activation="relu"),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(10),
        ]
    )
    loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
    model.compile(optimizer="adam", loss=loss_fn, metrics=["accuracy"])
    return model


@track_task_emissions(task_name="inference", tracker=tracker)
def predict(grid, x_test):
    grid.predict(x_test)


def main():
    mnist = tf.keras.datasets.mnist
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    x_train, x_test = x_train / 255.0, x_test / 255.0

    tracker.start()

    # First mode of task emission tracking, using explicit functions start_task & stop_task
    tracker.start_task("build model")
    model = KerasClassifier(build_fn=build_model, epochs=1)
    tracker.stop_task()
    param_grid = dict(batch_size=list(range(32, 256 + 32, 32)))

    # Track task emissions using the context manager
    with TaskEmissionsTracker(task_name="Grid search", tracker=tracker):
        grid = GridSearchCV(estimator=model, param_grid=param_grid)
    grid.fit(x_train, y_train)

    for _ in range(10):
        # Third tracking mode for tasks, use a decorated function with track_task_emissions decorator
        predict(grid, x_test)

    emissions = tracker.stop()

    print(f"Emissions : {emissions} kg CO₂")
    for task_name, task in tracker._tasks.items():
        print(
            f"Emissions : {task.emissions_data.emissions} kg CO₂ for task {task_name}"
        )


if __name__ == "__main__":
    main()
