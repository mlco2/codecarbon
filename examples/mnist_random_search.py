import kerastuner
import tensorflow as tf

from codecarbon import EmissionsTracker


class RandomSearchTuner(kerastuner.tuners.RandomSearch):
    def run_trial(self, trial, *args, **kwargs):
        # You can add additional HyperParameters for preprocessing and custom training loops
        # via overriding `run_trial`
        kwargs["batch_size"] = trial.hyperparameters.Int("batch_size", 32, 256, step=32)

        super().run_trial(trial, *args, **kwargs)


def build_model(hp):

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

    tuner = RandomSearchTuner(
        build_model,
        objective="val_accuracy",
        directory="random_search_results",
        project_name="codecarbon",
        max_trials=3,
    )

    tracker = EmissionsTracker(project_name="mnist_random_search")
    tracker.start()
    tuner.search(x_train, y_train, epochs=10, validation_data=(x_test, y_test))
    emissions = tracker.stop()

    print(f"Emissions : {emissions} kg CO₂")


if __name__ == "__main__":
    main()
