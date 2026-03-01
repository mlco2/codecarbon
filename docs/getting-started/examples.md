# Examples

Following are examples to train a Deep Learning model on MNIST Data to
recognize digits in images using TensorFlow.

## Using the Decorator

This is the simplest way to use the CodeCarbon tracker with two lines of
code. You just need to copy-paste `from codecarbon import track_emissions`
and add the `@track_emissions` decorator to your training function. The emissions will be tracked
automatically and printed at the end of the training.

But you can't get them in your code, see the Context Manager section
below for that.

``` python
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
```

## Using the Context Manager

We think this is the best way to use CodeCarbon. Still only two lines of
code, and you can get the emissions in your code.

``` python
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

# Display the emissions data
print(f"\nCarbon emissions from computation: {tracker.final_emissions * 1000:.4f} g CO2eq")
print("\nDetailed emissions data:", tracker.final_emissions_data)
```

## Using the Explicit Object

This is the recommended way to use the CodeCarbon tracker in a Notebook
: you instantiate the tracker and call the `start()` method
at the beginning of the Notebook. You call the `stop()` method at the end
of the Notebook to stop the tracker and get the emissions.

If not in an interactive Notebook, always use a
`try...finally` block to ensure that the tracker is stopped
even if an error occurs during training. This is important to ensure the
CodeCarbon scheduler is stopped. If you don't use
`try...finally`, the scheduler will continue running in the
background after your computation code has crashed, so your program will
never finish.

``` python
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
try:
    model.fit(x_train, y_train, epochs=10)
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    emissions: float = tracker.stop()
    print(emissions)
```

Other examples are available in the [project GitHub
repository](https://github.com/mlco2/codecarbon/tree/master/examples).
