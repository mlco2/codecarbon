from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

from codecarbon import EmissionsTracker

digits = datasets.load_digits()

# flatten the images
n_samples = len(digits.images)
data = digits.images.reshape((n_samples, -1))

# Create a classifier: a support vector classifier
model = MLPClassifier(
    hidden_layer_sizes=(128, 100),
    max_iter=1000,
    alpha=1e-4,
    solver="adam",
    random_state=1,
    learning_rate_init=0.2,
)

X_train, X_test, y_train, y_test = train_test_split(
    data, digits.target, test_size=0.1, shuffle=False
)

tracker = EmissionsTracker()
tracker.start()
# Learn the digits on the train subset
model.fit(X_train, y_train)
emissions: float = tracker.stop()
print(f"Emissions: {emissions} kg")
