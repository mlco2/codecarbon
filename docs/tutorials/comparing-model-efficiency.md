# Comparing Model Efficiency with Carbon Tracking

In this tutorial, you'll learn how to measure and compare the carbon emissions of different machine learning model configurations. By the end, you'll be able to identify which model offers the best trade-off between accuracy and environmental impact.

## Why This Matters

When training machine learning models, we often focus on accuracy or performance metrics. But as a data scientist, you can now measure the carbon cost of different approaches and make informed decisions about which model is truly efficient. Some configurations might achieve slightly higher accuracy while consuming significantly more energy—and it's worth knowing that trade-off.

## Setup

Before we start comparing models, let's get all the necessary imports in place. You'll need a few data science libraries (scikit-learn, pandas) and of course CodeCarbon itself:

``` python
import time
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

from codecarbon import EmissionsTracker

# Create output directory for emissions logs
from pathlib import Path
Path("./emissions").mkdir(exist_ok=True)
```

These are the tools we'll use:
- **scikit-learn** – for building and training machine learning models
- **pandas** – for organizing and analyzing results
- **CodeCarbon** – for measuring emissions
- **time** – to track how long training takes (for comparison)

## The Explicit Object Pattern for Long Experiments

For iterative experiments like model training, the explicit object pattern is perfect. You call `tracker.start()` at the beginning of training and `tracker.stop()` at the end. This approach gives you full control and is ideal when you're training multiple models in a loop.

**Key pattern:** Always use `try...finally` to ensure the tracker stops, even if an error occurs during training:

``` python
tracker = EmissionsTracker(project_name="my_experiment")
tracker.start()
try:
    # Your training code here
    pass
finally:
    emissions = tracker.stop()
```

This ensures CodeCarbon's internal scheduler is properly shut down, preventing background threads from running after your experiment finishes.

## Practical Example: Comparing Model Configurations

Now let's put this into practice. We'll compare three RandomForest configurations with different sizes to see how they balance accuracy and carbon emissions.

### Step 1: Generate a Synthetic Dataset

``` python skip
# Create a classification dataset
X, y = make_classification(
    n_samples=10000,
    n_features=20,
    n_informative=15,
    n_redundant=5,
    n_classes=3,
    random_state=42
)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Dataset: {X_train.shape[0]} training samples, {X_test.shape[0]} test samples")
print(f"Features: {X_train.shape[1]}, Classes: {len(np.unique(y))}")
```

### Step 2: Define Model Configurations

``` python skip
models_to_test = [
    {"name": "Small RF", "n_estimators": 50, "max_depth": 10},
    {"name": "Medium RF", "n_estimators": 100, "max_depth": 15},
    {"name": "Large RF", "n_estimators": 200, "max_depth": 20},
]
```

### Step 3: Train and Track Each Configuration

``` python skip
results = []

for model_config in models_to_test:
    print(f"\nTraining {model_config['name']}...")

    # Start emissions tracking
    tracker = EmissionsTracker(
        project_name=f"ml_{model_config['name'].replace(' ', '_').lower()}",
        output_dir="./emissions"
    )
    tracker.start()

    try:
        # Record training time
        start_time = time.time()

        # Train the model
        model = RandomForestClassifier(
            n_estimators=model_config["n_estimators"],
            max_depth=model_config["max_depth"],
            random_state=42,
            n_jobs=-1  # Use all available cores
        )

        model.fit(X_train, y_train)
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        training_time = time.time() - start_time

    finally:
        # Stop tracking (guaranteed to run even if error occurs)
        emissions = tracker.stop()
        if emissions is None:
            emissions = 0.0

        # Store results
        results.append({
            "Model": model_config["name"],
            "Train Accuracy": train_score,
            "Test Accuracy": test_score,
            "Training Time (s)": training_time,
            "CO2 Emissions (kg)": emissions,
            "CO2 per Accuracy Point": emissions / test_score if test_score > 0 else float("inf"),
        })

        print(f"✓ {model_config['name']}: {test_score:.3f} accuracy, {emissions:.6f} kg CO2")
```

## Analyzing Results

Now let's collect all results and analyze them:

``` python skip
# Create a DataFrame with results
df_results = pd.DataFrame(results)
print("\nModel Comparison Results:")
print("=" * 70)
print(df_results.to_string(index=False))

# Find the most efficient model
most_efficient = df_results.loc[df_results["CO2 per Accuracy Point"].idxmin()]
print(f"\nMost Carbon-Efficient Model: {most_efficient['Model']}")
print(f"  Efficiency Score: {most_efficient['CO2 per Accuracy Point']:.8f} kg CO2 per accuracy point")
print(f"  Test Accuracy: {most_efficient['Test Accuracy']:.3f}")
print(f"  CO2 Emissions: {most_efficient['CO2 Emissions (kg)']:.6f} kg")
```

## Visualizing Trade-offs

Let's create a 4-panel visualization to understand the trade-offs between different models:

``` python skip
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Model Efficiency Comparison", fontsize=16, fontweight="bold")

# Panel 1: CO2 Emissions by Model
axes[0, 0].bar(
    df_results["Model"],
    df_results["CO2 Emissions (kg)"],
    color=["#FF7F50", "#FFB347", "#90EE90"]
)
axes[0, 0].set_title("Carbon Emissions by Model")
axes[0, 0].set_ylabel("CO2 Emissions (kg)")
axes[0, 0].tick_params(axis="x", rotation=45)

# Panel 2: Accuracy vs Emissions (Trade-off Curve)
scatter = axes[0, 1].scatter(
    df_results["Test Accuracy"],
    df_results["CO2 Emissions (kg)"],
    s=200,
    c=range(len(df_results)),
    cmap="RdYlGn",
    alpha=0.7,
    edgecolors="black",
    linewidth=2
)
for i, model in enumerate(df_results["Model"]):
    axes[0, 1].annotate(
        model,
        (df_results["Test Accuracy"].iloc[i], df_results["CO2 Emissions (kg)"].iloc[i]),
        xytext=(8, 8),
        textcoords="offset points",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.3)
    )
axes[0, 1].set_title("Accuracy vs Emissions Trade-off")
axes[0, 1].set_xlabel("Test Accuracy")
axes[0, 1].set_ylabel("CO2 Emissions (kg)")
axes[0, 1].grid(True, alpha=0.3)

# Panel 3: Training Time vs Emissions
axes[1, 0].scatter(
    df_results["Training Time (s)"],
    df_results["CO2 Emissions (kg)"],
    s=200,
    c=range(len(df_results)),
    cmap="RdYlGn",
    alpha=0.7,
    edgecolors="black",
    linewidth=2
)
for i, model in enumerate(df_results["Model"]):
    axes[1, 0].annotate(
        model,
        (df_results["Training Time (s)"].iloc[i], df_results["CO2 Emissions (kg)"].iloc[i]),
        xytext=(8, 8),
        textcoords="offset points",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.3)
    )
axes[1, 0].set_title("Training Time vs Emissions")
axes[1, 0].set_xlabel("Training Time (seconds)")
axes[1, 0].set_ylabel("CO2 Emissions (kg)")
axes[1, 0].grid(True, alpha=0.3)

# Panel 4: Carbon Efficiency Score (Lower is Better)
axes[1, 1].bar(
    df_results["Model"],
    df_results["CO2 per Accuracy Point"],
    color=["#90EE90", "#FFB347", "#FF7F50"]  # Green=best, Red=worst
)
axes[1, 1].set_title("Carbon Efficiency (Lower is Better)")
axes[1, 1].set_ylabel("CO2 per Accuracy Point")
axes[1, 1].tick_params(axis="x", rotation=45)

plt.tight_layout()
plt.show()
```

## Key Patterns to Remember

**When to use the explicit object pattern:**
- Iterative experiments where you train multiple models in a loop
- Long-running Jupyter notebooks where you want fine-grained control
- Any scenario where your computation spans multiple cells or functions

**Best practices:**
- Always wrap your code in `try...finally` to ensure the tracker stops
- Use descriptive `project_name` values to organize your results later
- Set `output_dir` consistently so emissions data is easy to find
- Use `n_jobs=-1` in scikit-learn to leverage all CPU cores (and accurately measure energy consumption)

**Interpreting results:**
- **Emissions** alone isn't the full picture—consider accuracy and time together
- **CO2 per accuracy point** combines efficiency with model quality
- Small improvements in accuracy might require disproportionate energy increases
- The "best" model depends on your priorities (accuracy vs. environmental impact)

## What's Next?

You've now learned how to compare carbon efficiency across models. Here are some next steps:

- **Configure tracking options:** Customize tracking behavior with a `.codecarbon.config` file (see [How-to: Configuration](../how-to/configuration.md))
- **Send data to the cloud:** Upload your emissions data to the CodeCarbon dashboard for visualization (see [How-to: Cloud API](../how-to/cloud-api.md))
- **Track distributed training:** Monitor emissions across multiple machines (see [How-to: Slurm](../how-to/slurm.md))
- **Dive deeper:** Learn all CodeCarbon features in the [API Reference](../reference/api.md)

Remember: Measuring is the first step toward sustainable computing! 🌱
