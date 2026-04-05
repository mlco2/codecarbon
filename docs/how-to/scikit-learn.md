# Track Carbon Emissions with scikit-learn

scikit-learn is one of the most widely-used Python libraries for machine learning. CodeCarbon works seamlessly with scikit-learn models to measure the carbon impact of training classifiers, regressors, and other algorithms.

## Installation

```console
pip install codecarbon scikit-learn
```

## Basic Example

Here's how to track the carbon emissions of training a scikit-learn classifier:

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from codecarbon import EmissionsTracker

# Create a dataset
X, y = make_classification(n_samples=1000, n_features=20, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Track training emissions
with EmissionsTracker() as tracker:
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    accuracy = model.score(X_test, y_test)

print(f"Model accuracy: {accuracy:.3f}")
print(f"Training emissions: {tracker.final_emissions:.6f} kg CO2eq")
```

## What Gets Logged

When you run the example above, CodeCarbon creates an `emissions.csv` file in your working directory with columns including:

- `timestamp`: when the measurement was taken
- `duration`: how long the training took
- `emissions`: CO2 in kg
- `energy_kwh`: energy consumed in kilowatt-hours
- `cpu_power`: CPU power in watts
- `gpu_power`: GPU power in watts (if applicable)

## Comparing Different Models

To compare the carbon efficiency of different scikit-learn configurations, see [Comparing Model Efficiency](../tutorials/comparing-model-efficiency.md). That tutorial shows how to train multiple model variants and analyze their emissions trade-offs.

## Multiple Trackers

You can also track individual operations separately:

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from codecarbon import EmissionsTracker

# Create a dataset
X, y = make_classification(n_samples=1000, n_features=20, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

tracker = EmissionsTracker()
tracker.start()

try:
    # Training
    model = RandomForestClassifier(n_estimators=50)
    model.fit(X_train, y_train)
    training_emissions = tracker.stop()

    # Prediction
    tracker.start()
    predictions = model.predict(X_test)
    prediction_emissions = tracker.stop()

    print(f"Training emissions: {training_emissions:.6f} kg CO2eq")
    print(f"Prediction emissions: {prediction_emissions:.6f} kg CO2eq")
except Exception as e:
    tracker.stop()
    raise
```

## Next Steps

- [Configure CodeCarbon](configuration.md) to customize tracking behavior
- [Send emissions data to the cloud](cloud-api.md) to visualize across multiple runs
- Integrate with other frameworks: [Transformers](transformers.md) and [Diffusers](diffusers.md)
