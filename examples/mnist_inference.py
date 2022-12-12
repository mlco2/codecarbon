import tensorflow as tf
from sklearn.model_selection import GridSearchCV
from tensorflow.keras.wrappers.scikit_learn import KerasClassifier

from codecarbon import EmissionsTracker


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


def main():
    mnist = tf.keras.datasets.mnist
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    x_train, x_test = x_train / 255.0, x_test / 255.0

    tracker = EmissionsTracker(project_name="mnist_inference", measure_power_secs=1)
    tracker.start()
    tracker.start_task("build model")
    model = KerasClassifier(build_fn=build_model, epochs=1)
    tracker.stop_task("build model")
    param_grid = dict(batch_size=list(range(32, 256 + 32, 32)))
    tracker.start_task("Grid search")
    grid = GridSearchCV(estimator=model, param_grid=param_grid)
    grid.fit(x_train, y_train)
    tracker.stop_task("Grid search")

    for i in range(10):
        inference_task_name = "Inference_" + str(i)
        tracker.start_task(inference_task_name)
        grid.predict(x_test)
        tracker.stop_task(inference_task_name)

    emissions = tracker.stop()

    print(f"Emissions : {emissions} kg CO₂")
    for task_name, task in tracker._tasks.items():
        print(
            f"Emissions : {task.emissions_data.emissions} kg CO₂ for task {task_name}"
        )


if __name__ == "__main__":
    main()
