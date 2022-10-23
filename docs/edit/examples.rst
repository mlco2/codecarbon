.. _examples:

Examples
========

Following are examples to train a Deep Learning model on MNIST Data to recognize digits in images using TensorFlow.

Using the Explicit Object
-------------------------

.. code-block:: python

    import tensorflow as tf

    from codecarbon import EmissionsTracker

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

    tracker = EmissionsTracker()
    tracker.start()
    model.fit(x_train, y_train, epochs=10)
    emissions: float = tracker.stop()
    print(emissions)

Using the Context Manager
-------------------------

.. code-block:: python

    import tensorflow as tf

    from codecarbon import EmissionsTracker

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

    with EmissionsTracker() as tracker:
        model.compile(optimizer="adam", loss=loss_fn, metrics=["accuracy"])
        model.fit(x_train, y_train, epochs=10)


Using the Decorator
-------------------

.. code-block:: python

    import tensorflow as tf

    from codecarbon import track_emissions


    @track_emissions(project_name="mnist")
    def train_model():
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

        return model


    if __name__ == "__main__":
        model = train_model()


Others examples are available in the `project GitHub repository  <https://github.com/mlco2/codecarbon/tree/master/examples>`_.
