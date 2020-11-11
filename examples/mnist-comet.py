from comet_ml import Experiment  # isort:skip

import tensorflow as tf

## Assumes Comet variable environment configuration.
## See here to get your API_KEY:
## https://www.comet.ml/user/settings/account#section-DEVELOPER_INFORMATION
## And here for setup information:
## https://www.comet.ml/docs/python-sdk/advanced/#experiment-configuration-parameters
experiment = Experiment()

mnist = tf.keras.datasets.mnist

(x_train, y_train), (x_test, y_test) = mnist.load_data()
x_train, x_test = x_train / 255.0, x_test / 255.0

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

model.fit(x_train, y_train, epochs=10)
