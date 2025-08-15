import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    ConfusionMatrixDisplay,
)
from scipy.stats import skew, kurtosis
from scipy.signal import welch
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
from action_dataloader import dataloader

# Load EEG Data X = eeg, y = labels and info = metadata
X, y, info = dataloader()

# Encode Labels for Classification (["biting", "blink", "eyebrow", "jaw"] to [0,1,2,3])
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Feature Extraction
def extract_features(eeg_data, sfreq):
    """
    Extracts statistical and spectral features from EEG data.
    - eeg_data: (n_samples, n_channels, n_timepoints)
    - sfreq: Sampling frequency from MNE `info`
    Returns: (n_samples, n_features)
    """
    n_samples, n_channels, n_timepoints = eeg_data.shape
    features = []

    for sample in eeg_data:
        feature_vector = []

        # **Compute Power Spectral Density (PSD) Using Welch’s Method**
        for channel in sample:
            freqs, psd = welch(channel, sfreq, nperseg=min(256, len(channel)))
            feature_vector.extend([psd.mean()])
            feature_vector.extend([psd.std()])

        # Compute Time-Domain Statistics
        feature_vector.extend(sample.mean(axis=1).tolist())
        feature_vector.extend(sample.std(axis=1).tolist())
        feature_vector.extend(skew(sample, axis=1).tolist())
        feature_vector.extend(kurtosis(sample, axis=1).tolist())

        features.append(feature_vector)

    return np.array(features)


# Extract Features from EEG Data, verify dims (n_samples, n_features)
X_features = extract_features(X, info["sfreq"])
print(f"Feature matrix shape: {X_features.shape}")


# Extract Features from EEG Data
X_features = extract_features(X, info["sfreq"])
print(f"Feature matrix shape: {X_features.shape}")

# Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X_features,
    y_encoded,
    test_size=0.9,
    random_state=42,
    shuffle=True,
    stratify=y_encoded,
)

# Train a Random Forest Classifier - might have to change the type of classifier if needed
# clf = RandomForestClassifier(n_estimators=100, random_state=42) # results in 100% accuracy
clf = RandomForestClassifier(
    n_estimators=50,  # Reduce number of trees
    max_depth=10,  # Limit tree depth
    min_samples_split=5,  # Prevent too-specific splits
    random_state=42,
)
clf.fit(X_train, y_train)

# Evaluate the Model
y_pred = clf.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# Compute Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
labels = (
    label_encoder.classes_
)  # Retrieve class names: ["biting", "blink", "eyebrow", "jaw"]

# Plot Confusion Matrix with Labels
plt.figure(figsize=(6, 5))
sns.heatmap(
    cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels
)
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.title("Confusion Matrix")
plt.show()

# Save the model to a file named 'eeg_model.pkl'
joblib.dump(clf, 'project_directory/scripts/demo/classifier/models/eeg_model.pkl')