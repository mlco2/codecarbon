import tensorflow as tf
from sklearn.model_selection import GridSearchCV
from tensorflow.keras.wrappers.scikit_learn import KerasClassifier

from codecarbon import OfflineEmissionsTracker


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

    for country in ["CAN", "FRA", "GER", "USA"]:
        print("••• Grid Search Location:", country, end="\n\n")
        mnist = tf.keras.datasets.mnist
        (x_train, y_train), (x_test, y_test) = mnist.load_data()
        x_train, x_test = x_train / 255.0, x_test / 255.0

        model = KerasClassifier(build_fn=build_model, epochs=10)
        param_grid = dict(batch_size=list(range(32, 256 + 32, 32)))
        grid = GridSearchCV(estimator=model, param_grid=param_grid)

        tracker = OfflineEmissionsTracker(country_iso_code=country)
        tracker.start()
        grid_result = grid.fit(x_train, y_train)
        emissions = tracker.stop()

        print(emissions)
        print("Best: %f using %s" % (grid_result.best_score_, grid_result.best_params_))


if __name__ == "__main__":
    main()
